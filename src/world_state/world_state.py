from typing import Any, Iterable, ValuesView, Optional

from src.settings import Consts
from src.models.components import Controls, KeyPresses, GameObj
from src.models.data import DefaultIDs, Spell, Targeting
from src.models.events import FinalizedEvent, Outcome, UpcomingEvent
from ._event_log import EventLog
from ._aura_handler import AuraHandler
from ._frame_heap import FrameHeap
from ._game_obj_handler import GameObjHandler
from ._id_gen import IdGen
from ._spell_database import SpellDatabase


class WorldState:
    """ The entire game state of the save file that is currently in use """

    def __init__(self) -> None:
        self.spell_database: SpellDatabase = SpellDatabase()
        self._auras: AuraHandler = AuraHandler()
        self._game_objs: GameObjHandler = GameObjHandler()
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._event_log_for_each_frame: dict[int, EventLog] = {}

    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.view_game_objs
    @property
    def default_ids(self) -> DefaultIDs:
        return self._game_objs.default_ids
    @property
    def view_event_logs(self) -> dict[int, EventLog]:
        return self._event_log_for_each_frame

    def process_setup_events(self, ingame_time: int, setup_spell_ids: list[int]) -> None:
        source_id = self.default_ids.environment_id
        for setup_event in UpcomingEvent.create_setup_events(ingame_time, source_id, setup_spell_ids):
            self._event_heap.insert_event(setup_event)
        empty_list_of_player_input: list[KeyPresses] = []
        self.process_frame(empty_list_of_player_input, ingame_time)

    def process_frame(self, player_inputs: list[KeyPresses], frame_end: int) -> None:
        """Execute state updates for current frame"""
        for key_presses in player_inputs:
            if key_presses != KeyPresses.NONE:
                controls = Controls(obj_id=self.default_ids.player_id, timeline_timestamp=frame_end, key_presses=key_presses)
                player_obj = self._game_objs.get_game_obj(controls.obj_id)
                for controls_event in UpcomingEvent.create_events_from_controls(player_obj, controls):
                    self._event_heap.insert_event(controls_event)
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
        self._event_log_for_each_frame[frame_end] = event_log

    def _fetch_cascading_events(self, f_event: FinalizedEvent, new_obj: Optional[GameObj]) -> Iterable[UpcomingEvent]:
        if new_obj is not None and f_event.spell.spawned_obj is not None and f_event.spell.spawned_obj.obj_controls is not None:
            for controls in f_event.spell.copy_obj_controls:
                controls.increase_offset(new_obj.loadout.spawn_timestamp)
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
        spell = self.spell_database.get_spell(event.spell_id)
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