from dataclasses import dataclass

from src.settings import Consts
from .event_handler import EventHandler, IdGen
from .state_handler import StateHandler, DisplayObj, InputRegistry
from .state_handler.visuals_system import SpellVisualsData


@dataclass(slots=True)
class FrameOutput:
    effect_id: int
    scale: float
    pos_x: float
    pos_y: float
    is_visible: bool
    color_red: int
    color_green: int
    color_blue: int
    sprite_name: str
    animation_name: str
    audio_name: str



class WorldState:
    """ The entirely ECS-driven game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._event_handler: EventHandler = EventHandler()
        self._state_handler: StateHandler = StateHandler()
        self._create_environment_obj()

    def get_display_obj_dct(self, current_time: int) -> dict[int, DisplayObj]:
        display_obj_dct: dict[int, DisplayObj] = {}
        obj_ids = self._state_handler.active_obj_ids
        for obj_id in obj_ids:
            display_obj = self._state_handler.create_display_obj(current_time, obj_id)
            display_obj_dct[obj_id] = display_obj
        return display_obj_dct

    def get_combat_interactions_for_frame(self, current_frame_time: int) -> list[tuple[int, int, int]]:
        return self._event_handler.get_combat_interactions_for_frame(current_frame_time)

    def get_spell_vfx_for_successful_events(self, timestamp: int) -> list[SpellVisualsData]:
        spell_visuals_data: list[SpellVisualsData] = []
        combat_interactions = self._event_handler.get_combat_interactions_for_frame(timestamp)
        for _, spell_id, _ in combat_interactions:
            spell_visuals = self._state_handler.get_spell_visuals(spell_id)
            #if spell_vfx.animate_on_source or spell_vfx.animate_on_target:
            #    self, source_id: int, spell_id: int, target_id: int
            spell_visuals_data.append(spell_visuals)
        return spell_visuals_data

    def process_setup_events(self, ingame_time: int, setup_spell_ids: list[int]) -> None:
        environment_id = self._state_handler.environment_id
        for spell_id in setup_spell_ids:
            self._event_handler.dispatch_upcoming_event(ingame_time, environment_id, spell_id, environment_id)
        empty_list_of_player_inputs: list[str] = []
        self.process_frame(empty_list_of_player_inputs, ingame_time)

    def process_frame(self, player_inputs: list[str], frame_end: int) -> None:
        """Execute state updates for current frame"""
        self._create_events_from_controls(player_inputs, frame_end)
        while self._event_handler.has_unprocessed_events(frame_end):
            self._event_handler.fetch_next_event()
            timestamp = self._event_handler.current_events_timestamp
            source_id = self._event_handler.current_events_source_id
            spell_id = self._event_handler.current_events_spell_id
            target_id = self._event_handler.current_events_target_id
            assert timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {timestamp}."
            event_is_valid = self._validate_event(timestamp, source_id, spell_id, target_id)
            if event_is_valid:
                new_obj_id = self._handle_spawn(timestamp, source_id, spell_id, target_id)
                self._create_cascading_events(timestamp, new_obj_id, source_id, spell_id)
                self._apply_event(timestamp, source_id, spell_id, target_id)
        self._event_handler.finalize_event_log_for_current_frame(frame_end)

    def _create_cascading_events(self, timestamp: int, new_obj_id: int, source_id: int, spell_id: int) -> None:
        timeline = self._state_handler.get_ability_timeline(spell_id)
        if not timeline:
            return
        # Determine who casts the timeline events
        if new_obj_id != Consts.EMPTY_ID:
            t_source = new_obj_id
        else:
            t_source = source_id
        # Dispatch
        for trigger_timestamp, timeline_spell_ids in timeline.items():
            for t_spell in timeline_spell_ids:
                # Determine targets
                if self._state_handler.is_area_of_effect(spell_id):
                    timeline_targets = list(self._state_handler.select_targets_for_aoe(t_source, spell_id))
                else:
                    timeline_targets = [self._state_handler.get_current_target_for_obj(t_source)]
                for t_target in timeline_targets:
                    self._event_handler.dispatch_upcoming_event(
                        timestamp + trigger_timestamp, t_source, t_spell, t_target
                    )

    def _create_events_from_controls(self, player_inputs: list[str], timestamp: int) -> None:
        source_id = self._state_handler.player_id
        if not player_inputs or source_id == Consts.EMPTY_ID:
            return
        spell_ids = InputRegistry.get_spells_for_inputs(player_inputs)
        target_id = self._state_handler.get_current_target_for_obj(source_id)
        for spell_id in spell_ids:
            self._event_handler.dispatch_upcoming_event(timestamp, source_id, spell_id, target_id)

    def _validate_event(self, timestamp: int, source_id: int, spell_id: int, finalized_target_id: int) -> bool:
        if not self._state_handler.is_valid_source(source_id):
            self._event_handler.assign_outcome_source_is_disabled(finalized_target_id)
            return False
        elif not self._state_handler.is_gcd_ready(source_id, spell_id, timestamp):
            self._event_handler.assign_outcome_gcd_not_ready(finalized_target_id)
            return False
        elif not self._state_handler.is_cooldown_ready(source_id, spell_id, timestamp):
            self._event_handler.assign_outcome_cooldown_not_ready(finalized_target_id)
            return False
        elif not self._state_handler.is_valid_target(finalized_target_id) and not source_id == finalized_target_id:
            self._event_handler.assign_outcome_invalid_target(finalized_target_id)
            return False
        elif not self._state_handler.is_within_range(timestamp, source_id, spell_id, finalized_target_id):
            self._event_handler.assign_outcome_out_of_range(finalized_target_id)
            return False
        else:
            self._event_handler.assign_outcome_success(finalized_target_id)
            return True

    def _apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        self._state_handler.apply_event(timestamp, source_id, spell_id, target_id)

    def _handle_spawn(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        new_obj_id = Consts.EMPTY_ID
        if self._state_handler.is_obj_spawn(spell_id):
            new_obj_id = self._game_obj_id_gen.generate_new_id()
            self._state_handler.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id, target_id)
        return new_obj_id

    def _create_environment_obj(self) -> None:
        obj_id = self._game_obj_id_gen.generate_new_id()
        self._state_handler.create_environment_obj(obj_id)