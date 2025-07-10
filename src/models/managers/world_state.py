from typing import Iterable, ValuesView, Optional

from src.config import Consts
from src.models.components import Controls, GameObj
from src.models.configs import DefaultIDs, Spell, Targeting
from src.models.events import FinalizedEvent, Outcome, UpcomingEvent
from src.models.handlers import AuraHandler, EventLog, FrameHeap, GameObjHandler, IdGen, SpellDatabase


class WorldState:
    """ The entire game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._auras: AuraHandler = AuraHandler()
        self._game_objs: GameObjHandler = GameObjHandler()
        self._spell_database: SpellDatabase = SpellDatabase()
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.view_game_objs
    @property
    def default_ids(self) -> DefaultIDs:
        return self._game_objs.default_ids

    def try_add_player_input(self, player_input: Controls, timestamp: int) -> None:
        if player_input.is_empty:
            return
        player_input.timeline_timestamp = timestamp
        player_input.obj_id = self.default_ids.player_id
        player_obj = self._game_objs.get_game_obj(player_input.obj_id)
        for controls_event in UpcomingEvent.create_events_from_controls(player_obj, player_input):
            self._event_heap.insert_event(controls_event)

    def process_frame(self, frame_end: int) -> EventLog:
        """Execute state updates for current frame"""
        event_log = EventLog()
        while self._event_heap.has_unprocessed_events(frame_end):
            u_event = self._event_heap.pop_next_event()
            assert u_event.timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {u_event}."
            f_event = self._finalize_event(u_event, self._event_id_gen.generate_new_id())
            event_log.log_event(f_event)
            if f_event.outcome_is_valid:
                new_obj = self._game_objs.handle_spawn(f_event)
                self._auras.handle_aura(f_event)
                if f_event.spell.has_cascading_events:
                    for cascading_event in self._fetch_cascading_events(f_event, new_obj):
                        self._event_heap.insert_event(cascading_event)
                self._game_objs.modify_game_obj(f_event)
        return event_log

    def _fetch_cascading_events(self, f_event: FinalizedEvent, new_obj: Optional[GameObj]) -> Iterable[UpcomingEvent]:
        if new_obj is not None and f_event.spell.obj_controls is not None:
            for controls in f_event.spell.copy_obj_controls:
                controls.increase_offset(new_obj.cds.spawn_timestamp)
                yield from UpcomingEvent.create_events_from_controls(new_obj, controls)
        if f_event.spell.is_area_of_effect and not f_event.upcoming_event.is_aoe_targeting:
            target_ids = Targeting.select_targets_for_aoe(f_event.source, f_event.target, self.view_game_objs)
            yield from f_event.upcoming_event.create_aoe_events(target_ids)
        if f_event.spell.spell_sequence is not None:
            yield from f_event.upcoming_event.create_spell_sequence_events(f_event.spell.spell_sequence)
        if f_event.spell.has_aura_apply:
            aura = self._auras.get_aura(f_event.source_id, f_event.spell_id, f_event.target_id)
            yield from UpcomingEvent.create_aura_tick_events(aura)

    def _finalize_event(self, event: UpcomingEvent, event_id: int) -> FinalizedEvent:
        source_obj = self._game_objs.get_game_obj(event.source_id)
        spell = self._spell_database.get_spell(event.spell_id)
        target_obj = self._decide_event_target(event, source_obj, spell)
        if event.is_aura_tick and not self._auras.aura_exists(event):
            outcome = Outcome.AURA_NO_LONGER_EXISTS
        else:
            event.source_id = source_obj.obj_id
            event.target_id = target_obj.obj_id
            outcome = Outcome.decide_outcome(event.timestamp, source_obj, spell, target_obj, event.is_aoe_targeting)
        finalized_event = FinalizedEvent(event_id=event_id, source=source_obj, spell=spell, target=target_obj, upcoming_event=event, outcome=outcome)
        return finalized_event

    def _decide_event_target(self, event: UpcomingEvent, source_obj: GameObj, spell: Spell) -> GameObj:
        if event.is_aoe_targeting:
            target_id = event.target_id
        else:
            target_id = spell.targeting.select_target(source_obj, self.default_ids)
        if target_id == source_obj.obj_id:
            return source_obj
        if spell.is_target_of_target and Consts.is_valid_id(target_id):
            obj_with_target_to_copy = self._game_objs.get_game_obj(target_id)
            if Consts.is_valid_id(obj_with_target_to_copy.current_target):
                target_id = obj_with_target_to_copy.current_target
            else:
                target_id = self.default_ids.missing_target_id
        return self._game_objs.get_game_obj(target_id)

    def _process_setup_events(self, ingame_time: int, setup_spell_ids: list[int]) -> dict[int, EventLog]:
        source_id = self.default_ids.environment_id
        for setup_event in UpcomingEvent.create_setup_events(ingame_time, source_id, setup_spell_ids):
            self._event_heap.insert_event(setup_event)
        event_log = self.process_frame(ingame_time)
        return {ingame_time: event_log}