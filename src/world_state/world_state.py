from typing import Any, Iterable, Optional
from dataclasses import dataclass

from src.settings import Consts
from src.world_state._spell_database import SpellDatabase
from ._event_log import EventLog
from ._frame_heap import FrameHeap
from ._id_gen import IdGen
from ._event_system import UpcomingEvent, Outcome
from ._spell_database import SpellDatabase
from ._casting_system import CastingSystem
from ._combat_system import CombatSystem
from ._movement_system import MovementSystem
from ._targeting_system import TargetingSystem
from ._vfx_and_sfx_system import VfxAndSfxSystem, SpellVfxData



@dataclass(slots=True)
class DisplayObj:
    obj_id: int
    pos_xy: tuple[float, float]
    size: float
    color_rgb: tuple[int, int, int]
    sprite_name: str


class WorldState:
    """ The entirely ECS-driven game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 100_000)
        self._event_log_for_each_frame: dict[int, EventLog] = {}

        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self.spell_database: SpellDatabase = SpellDatabase()
        self._combat_system = self.spell_database.create_combat_system()
        self._casting_system = self.spell_database.create_casting_system()
        self._movement_system = self.spell_database.create_movement_system()
        self._targeting_system = self.spell_database.create_targeting_system()
        self._vfx_and_sfx_system = self.spell_database.create_vfx_and_sfx_system()

        self._create_environment_obj()

    @property
    def view_event_logs(self) -> dict[int, EventLog]:
        return self._event_log_for_each_frame

    def view_display_objs(self, current_time: int) -> Iterable[DisplayObj]:
        for obj_id in self._targeting_system.game_obj_data_dct.keys():
            obj_vfx = self._vfx_and_sfx_system.get_obj_visuals(obj_id)
            if not self._targeting_system.is_visible(obj_id) or not obj_vfx:
                continue
            x, y = self._movement_system.get_position(obj_id, current_time)
            yield DisplayObj(obj_id, (x, y), self._combat_system.get_size(obj_id), obj_vfx.color, obj_vfx.sprite_name)

    def get_spell_vfx_for_successful_events(self, timestamp: int) -> Iterable[SpellVfxData]:
        for spell_id in self._event_log_for_each_frame[timestamp].get_successful_spell_ids:
            yield self._vfx_and_sfx_system.get_spell_visuals(spell_id)

    def process_setup_events(self, ingame_time: int, setup_spell_ids: list[int]) -> None:
        environment_id = self._targeting_system.environment_id
        for spell_id in setup_spell_ids:
            event_id=self._event_id_gen.generate_new_id()
            setup_event = UpcomingEvent(event_id, ingame_time, environment_id, spell_id)
            self._event_heap.insert_event(setup_event)
        empty_list_of_player_inputs: list[str] = []
        self.process_frame(empty_list_of_player_inputs, ingame_time)

    def process_frame(self, player_inputs: list[str], frame_end: int) -> None:
        """Execute state updates for current frame"""
        for controls_event in self._create_events_from_controls(player_inputs, frame_end):
            self._event_heap.insert_event(controls_event)
        event_log = EventLog()
        while self._event_heap.has_unprocessed_events(frame_end):
            u_event = self._event_heap.pop_next_event()
            timestamp = u_event.timestamp
            source_id = u_event.source_id
            spell_id = u_event.spell_id
            undecided_target_id = u_event.target_id
            assert timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {timestamp}."
            target_id = self._targeting_system.decide_event_targeting(source_id, spell_id, undecided_target_id)
            outcome = self._decide_outcome(timestamp, source_id, spell_id, target_id)
            if outcome.is_success:
                new_obj_id = self._handle_spawn(timestamp, source_id, spell_id, target_id)
                for cascading_event in self._fetch_cascading_events(timestamp, new_obj_id, source_id, spell_id, target_id):
                    self._event_heap.insert_event(cascading_event)
                self._apply_event(timestamp, source_id, spell_id, target_id)
            event_log.log_event(u_event, target_id, outcome)
        self._event_log_for_each_frame[frame_end] = event_log

    def _fetch_cascading_events(self, timestamp: int, new_obj_id: int, source_id: int, spell_id: int, target_id: int) -> Iterable[UpcomingEvent]:
        # 1. Spawned Object Control Events
        if new_obj_id != Consts.EMPTY_ID:
            new_obj_target_id = self._targeting_system.get_current_target_for_obj(new_obj_id)
            timeline = (self._casting_system.get_ability_timeline(spell_id))
            for trigger_timestamp, timeline_spell_ids in timeline.items():
                if isinstance(timeline_spell_ids, int):
                    timeline_spell_ids = (timeline_spell_ids,)
                for timeline_spell_id in timeline_spell_ids:
                    new_event_id = self._event_id_gen.generate_new_id()
                    new_timestamp = trigger_timestamp+timestamp
                    yield UpcomingEvent(new_event_id, new_timestamp, new_obj_id, timeline_spell_id, new_obj_target_id)
        # 2. Area of Effect (AoE) Events
        if self._targeting_system.is_area_of_effect(spell_id):
            effect_id = self._casting_system.get_effect_id(spell_id)
            target_ids = self._targeting_system.select_targets_for_aoe(source_id, target_id)
            for aoe_target_id in target_ids:
                new_event_id = self._event_id_gen.generate_new_id()
                yield UpcomingEvent(new_event_id, timestamp, source_id, effect_id, aoe_target_id)
        # 3. Spell Sequence Events
        sequenced_spells = self._casting_system.get_spell_sequence(spell_id)
        if sequenced_spells is not None:
            for next_spell_id in sequenced_spells:
                new_event_id = self._event_id_gen.generate_new_id()
                yield UpcomingEvent(new_event_id, timestamp, source_id, next_spell_id, target_id)
        # 4. Channel Tick Events
        if self._casting_system.has_channel_start(spell_id):
            effect_id = self._casting_system.get_effect_id(spell_id)
            for tick_timestamp in self._casting_system.get_tick_timestamps(timestamp, spell_id):
                new_event_id = self._event_id_gen.generate_new_id()
                yield UpcomingEvent(new_event_id, tick_timestamp, source_id, effect_id, target_id)


    def _create_events_from_controls(self, player_inputs: list[str], timestamp: int) -> Iterable[UpcomingEvent]:
        source_id = self._targeting_system.player_id
        if not player_inputs or source_id == Consts.EMPTY_ID:
            return
        target_id = self._targeting_system.get_current_target_for_obj(self._targeting_system.player_id)
        spell_ids = self._casting_system.get_spell_ids_for_inputs(source_id, player_inputs)
        for spell_id in spell_ids:
            event_id: int = self._event_id_gen.generate_new_id()
            yield UpcomingEvent(event_id, timestamp, source_id, spell_id, target_id)


    def _decide_outcome(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> Outcome:
        if not self._targeting_system.is_valid_source(source_id):
            return Outcome.SOURCE_IS_DISABLED
        if not self._casting_system.is_gcd_ready(source_id, spell_id, timestamp):
            return Outcome.GCD_NOT_READY
        if not self._targeting_system.is_valid_target(target_id) and not source_id == target_id:
            return Outcome.TARGET_IS_INVALID
        if not self._movement_system.is_within_range(timestamp, source_id, spell_id, target_id):
            return Outcome.OUT_OF_RANGE
        return Outcome.SUCCESS

    def _apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        self._casting_system.apply_casting_event(timestamp, source_id, spell_id)
        self._combat_system.apply_combat_event(source_id, spell_id, target_id)
        self._movement_system.apply_movement_event(timestamp, source_id, spell_id, target_id)
        self._targeting_system.apply_targeting_event(source_id, spell_id, target_id)

    def _handle_spawn(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        new_obj_id = Consts.EMPTY_ID
        if self._targeting_system.is_obj_spawn(spell_id):
            new_obj_id = self._game_obj_id_gen.generate_new_id()
            self._movement_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id)
            self._casting_system.spawn_game_obj(timestamp, new_obj_id, spell_id)
            self._combat_system.spawn_game_obj(new_obj_id, spell_id)
            self._targeting_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id, target_id)
            self._vfx_and_sfx_system.spawn_game_obj(new_obj_id, spell_id)
        return new_obj_id

    def _create_environment_obj(self) -> None:
        obj_id = self._game_obj_id_gen.generate_new_id()
        self._casting_system.create_environment_obj(obj_id)
        self._combat_system.create_environment_obj(obj_id)
        self._movement_system.create_environment_obj(obj_id)
        self._targeting_system.create_environment_obj(obj_id)
        self._vfx_and_sfx_system.create_environment_obj(obj_id)