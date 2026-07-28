from typing import Any, Iterable, ValuesView, Optional
from webbrowser import Galeon

from src.settings import Consts
from src.models.components import Controls, KeyPresses, GameObj
from src.world_state.spell_system import DefaultIDs, Spell
from src.models.events import Outcome, UpcomingEvent, Aura
from src.world_state.spell_system import Behavior
from ._aura_handler import AuraHandler
from ._event_log import EventLog
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
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 100_000)
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
        for setup_event in self._create_setup_events(ingame_time, source_id, setup_spell_ids):
            self._event_heap.insert_event(setup_event)
        empty_list_of_player_inputs: list[KeyPresses] = []
        self.process_frame(empty_list_of_player_inputs, ingame_time)

    def process_frame(self, player_inputs: list[KeyPresses], frame_end: int) -> None:
        """Execute state updates for current frame"""
        for key_presses in player_inputs:
            if key_presses != KeyPresses.NONE:
                controls = Controls(obj_id=self.default_ids.player_id, timeline_timestamp=frame_end, key_presses=key_presses)
                player_obj = self._game_objs.get_game_obj(controls.obj_id)
                for controls_event in self._create_events_from_controls(player_obj, controls):
                    self._event_heap.insert_event(controls_event)
        event_log = EventLog()
        while self._event_heap.has_unprocessed_events(frame_end):
            u_event = self._event_heap.pop_next_event()
            assert u_event.timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {u_event}."
            f_event = self._finalize_and_process_event(u_event)
            event_log.log_event(f_event)
        self._event_log_for_each_frame[frame_end] = event_log

    def _finalize_and_process_event(self, u_event: UpcomingEvent) -> UpcomingEvent:
        source_obj = self._game_objs.get_game_obj(u_event.source_id)
        spell = self.spell_database.get_spell(u_event.spell_id)
        target_obj = self._decide_event_target(u_event.target_id, u_event.is_aoe_targeting, source_obj, spell)
        expired_aura = u_event.is_aura_tick and not self._auras.aura_exists(u_event)
        outcome = WorldState._decide_outcome(u_event.timestamp, source_obj, spell, target_obj, expired_aura, u_event.is_aoe_targeting)
        f_event = u_event.finalize_event(source_obj.obj_id, target_obj.obj_id, outcome)
        self._process_event(f_event, source_obj, spell, target_obj)
        return f_event


    def _process_event(self, f_event: UpcomingEvent, source_obj: GameObj, spell: Spell, target_obj: GameObj) -> None:
        timestamp = f_event.timestamp
        source_id = source_obj.obj_id
        target_id = target_obj.obj_id
        if f_event.outcome_is_valid:
            new_obj = self._game_objs.handle_spawn(timestamp, source_obj, spell, target_id)
            if spell.has_aura_cancel:
                self._auras.remove_aura(source_id, spell.effect_id, target_id)
            new_aura_id = Consts.EMPTY_ID
            if spell.has_aura_apply:
                new_aura_id = self._auras.add_aura(timestamp, source_id, spell, target_id)
            if spell.has_cascading_events:
                for cascading_event in self._fetch_cascading_events(f_event, new_obj, source_obj, spell, target_obj, new_aura_id):
                    self._event_heap.insert_event(cascading_event)
            GameObjHandler.modify_game_obj(timestamp, source_obj, spell, target_obj)

    def _fetch_cascading_events(self, u_event: UpcomingEvent, new_obj: Optional[GameObj], source: GameObj, spell: Spell, target: GameObj, new_aura_id: int) -> Iterable[UpcomingEvent]:
        if new_obj is not None and spell.spawned_obj is not None and spell.spawned_obj.obj_controls is not None:
            for controls in spell.copy_obj_controls:
                controls.increase_offset(new_obj.get_spawn_timestamp())
                yield from self._create_events_from_controls(new_obj, controls)
        if spell.is_area_of_effect and not u_event.is_aoe_targeting:
            target_ids = self._select_targets_for_aoe(source, target, self.view_game_objs)
            yield from self._create_aoe_events(u_event, target_ids)
        if spell.spell_sequence is not None:
            yield from self._create_spell_sequence_events(u_event, spell.spell_sequence)
        if spell.has_aura_apply:
            #aura = self._auras.get_aura_by_key(source.obj_id, spell.spell_id, target.obj_id)
            aura = self._auras.get_aura_by_id(new_aura_id)
            yield from self._create_aura_tick_events(aura)

    def _decide_event_target(self, aoe_target_id: int, is_aoe_targeting: bool, source_obj: GameObj, spell: Spell) -> GameObj:
        if is_aoe_targeting:
            target_id = aoe_target_id
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

    # The below methods are for upcoming_event creation
    def _create_aoe_events(self, u_event: UpcomingEvent, target_ids: Iterable[int]) -> Iterable[UpcomingEvent]:
        priority = u_event.priority
        for target_id in target_ids:
            priority += 1
            yield self._helper_for_create_aoe_events(u_event, target_id, priority)

    def _helper_for_create_aoe_events(self, u_event: UpcomingEvent, target_id: int, priority: int) -> UpcomingEvent:
        aoe_copy = u_event.create_copy()
        aoe_copy.event_id = self._event_id_gen.generate_new_id()
        aoe_copy.priority = priority
        aoe_copy.target_id = target_id
        aoe_copy.is_aoe_targeting = True
        return aoe_copy

    def _create_spell_sequence_events(self, u_event: UpcomingEvent, spell_sequence_ids: tuple[int, ...]) -> Iterable[UpcomingEvent]:
        priority = u_event.priority
        for next_spell_id in spell_sequence_ids:
            priority += 1
            yield self._helper_for_create_spell_sequence_events(u_event, next_spell_id, priority)

    def _helper_for_create_spell_sequence_events(self, u_event: UpcomingEvent, spell_sequence_id: int, priority: int) -> UpcomingEvent:
        seq_copy = u_event.create_copy()
        seq_copy.event_id = self._event_id_gen.generate_new_id()
        seq_copy.priority = priority
        seq_copy.spell_id = spell_sequence_id
        seq_copy.is_spell_sequence = True
        return seq_copy

    def _create_events_from_controls(self, source: GameObj, controls: Controls) -> Iterable[UpcomingEvent]:
        input_event_order = 0
        for spell_id in source.convert_controls_to_spell_ids(controls, source.obj_id):
            input_event_order += 1
            assert spell_id != Consts.EMPTY_ID, f"Controls for {source.obj_id} is casting empty spell ID, fix spell configs."
            yield self._helper_for_create_event_from_control(source.obj_id, source.current_target, controls.ingame_time, spell_id, input_event_order)

    def _helper_for_create_event_from_control(self, source_obj_id: int, source_current_target: int, controls_ingame_time: int, spell_id: int, priority: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=self._event_id_gen.generate_new_id(),
            timestamp=controls_ingame_time,
            source_id=source_obj_id,
            spell_id=spell_id,
            target_id=source_current_target,
            priority=priority,
        )

    def _create_aura_tick_events(self, aura: Aura) -> Iterable[UpcomingEvent]:
        """ Return an event for each tick happening this frame, excluding frame_start, including frame_end """
        priority = 0
        for tick_timestamp in aura.tick_timestamps:
            priority += 1
            yield self._helper_for_create_aura_tick_event(aura, tick_timestamp, priority)


    def _helper_for_create_aura_tick_event(self, aura: Aura, tick_timestamp: int, priority: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=self._event_id_gen.generate_new_id(),
            timestamp=tick_timestamp,
            source_id=aura.source_id,
            spell_id=aura.periodic_spell_id,
            target_id=aura.target_id,
            priority=priority,
            aura_id=aura.aura_id,
            aura_origin_spell_id=aura.origin_spell_id,
            aura_start_time=aura.start_time,
        )


    def _create_setup_events(self, timestamp: int, source_id: int, setup_spell_ids: list[int]) -> Iterable[UpcomingEvent]:
        for spell_id in setup_spell_ids:
            yield self._helper_for_create_setup_event(timestamp, source_id, spell_id)


    def _helper_for_create_setup_event(self, timestamp: int, source_id: int, spell_id: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=self._event_id_gen.generate_new_id(),
            timestamp=timestamp,
            source_id=source_id,
            spell_id=spell_id
        )

    @staticmethod
    def _select_targets_for_aoe(source: GameObj, target: GameObj, all_game_objs: ValuesView[GameObj]) -> Iterable[int]:
        for obj in all_game_objs:
            team_is_hit_by_aoe = (
                (obj.is_on_players_team == source.is_on_players_team)
                == (source.is_on_players_team == target.is_on_players_team)
            )
            if team_is_hit_by_aoe and obj.is_valid_target and obj.obj_id != target.obj_id:
                yield obj.obj_id

    @staticmethod
    def _decide_outcome(timestamp: int, source_obj: GameObj, spell: Spell, target_obj: GameObj, expired_aura: bool, is_aoe_targeting: bool) -> Outcome:
        # If triggered from aura, ensure aura is still active
        if expired_aura:
            return Outcome.AURA_NO_LONGER_EXISTS
        # Validate source
        if not is_aoe_targeting:  # This was previously validated if AoE
            if not source_obj.is_valid_source:
                return Outcome.SOURCE_IS_DISABLED
            if not WorldState._gcd_is_available(timestamp, source_obj, spell):
                return Outcome.GCD_NOT_READY
        # Validate target
        if not target_obj.is_valid_target and not source_obj.obj_id == target_obj.obj_id:
            return Outcome.TARGET_IS_INVALID
        # Validate source relative to target
        if not WorldState._is_within_range(source_obj, spell, target_obj):
            return Outcome.OUT_OF_RANGE
        # More outcome conditions to be added here.
        return Outcome.SUCCESS

    @staticmethod
    def _is_within_range(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> bool:
        if not spell.has_range_limit:
            return True
        return source_obj.is_within_range_of(target_obj, spell.range_limit)

    @staticmethod
    def _gcd_is_available(timestamp: int, source_obj: GameObj, spell: Spell) -> bool:
        if not spell.flags & Behavior.TRIGGER_GCD:
            return True
        return source_obj.get_gcd_progress(timestamp) >= 1.0