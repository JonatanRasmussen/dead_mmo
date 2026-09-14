from typing import Any

from dataclasses import dataclass

from src.settings import Consts
from .event_handler import EventHandler, IdGen
from .state_handler import StateHandler, DisplayObj, DisplaySpell

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
    def __init__(self) -> None:
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._event_handler: EventHandler = EventHandler()
        self._state_handler: StateHandler = StateHandler()

    def get_display_obj_dct(self, current_time: int) -> dict[int, DisplayObj]:
        display_obj_dct: dict[int, DisplayObj] = {}
        obj_ids = self._state_handler.active_obj_ids
        for obj_id in obj_ids:
            display_obj_dct[obj_id] = self._state_handler.create_display_obj(current_time, obj_id)
        return display_obj_dct

    def get_combat_interactions_for_frame(self, current_frame_time: int) -> list[tuple[int, int, int]]:
        return self._event_handler.get_combat_interactions_for_frame(current_frame_time)

    def get_spell_vfx_for_successful_events(self, timestamp: int) -> list[DisplaySpell]:
        spell_visuals_data: list[DisplaySpell] = []
        combat_interactions = self._event_handler.get_combat_interactions_for_frame(timestamp)
        for _, spell_id, _ in combat_interactions:
            display_spell = self._state_handler.create_display_spell(spell_id)
            if display_spell:
                spell_visuals_data.append(display_spell)
        return spell_visuals_data

    def process_setup_events(self, ingame_time: int, setup_spell_ids: list[int]) -> None:
        environment_id = self._game_obj_id_gen.generate_new_id()
        self._state_handler.create_environment_obj(environment_id)
        for spell_id in setup_spell_ids:
            self._event_handler.dispatch_upcoming_event(ingame_time, environment_id, spell_id, environment_id)
        player_inputs: list[str] = []
        self.process_frame(player_inputs, ingame_time)

    def process_frame(self, player_inputs: list[str], frame_end: int) -> None:
        self._create_events_from_controls(player_inputs, frame_end)

        while self._event_handler.has_unprocessed_events(frame_end):
            self._event_handler.fetch_next_event()

            timestamp = self._event_handler.current_events_timestamp
            source_id = self._event_handler.current_events_source_id
            spell_id = self._event_handler.current_events_spell_id
            target_id = self._event_handler.current_events_target_id
            assert timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {timestamp}."

            validation_code = self._state_handler.validate_event(timestamp, source_id, spell_id, target_id)
            outcome_is_valid = self._event_handler.finalize_event(validation_code)

            if outcome_is_valid:
                self._handle_spawn(timestamp, source_id, spell_id, target_id)
                self._create_cascading_events(timestamp, source_id, spell_id)
                self._apply_event(timestamp, source_id, spell_id, target_id)

        self._event_handler.finalize_event_log_for_current_frame(frame_end)

    def _create_cascading_events(self, timestamp: int, source_id: int, spell_id: int) -> None:
        timeline = self._state_handler.get_ability_timeline(spell_id)
        if not timeline: return

        for trigger_timestamp, timeline_spell_ids in timeline.items():
            for t_spell in timeline_spell_ids:
                if self._state_handler.is_area_of_effect(spell_id):
                    timeline_targets = list(self._state_handler.select_targets_for_aoe(source_id, spell_id))
                else:
                    timeline_targets = [self._state_handler.get_current_target_for_obj(source_id)]
                for t_target in timeline_targets:
                    self._event_handler.dispatch_upcoming_event(timestamp + trigger_timestamp, source_id, t_spell, t_target)

    def _create_events_from_controls(self, player_inputs: list[str], timestamp: int) -> None:
        source_id = self._state_handler.player_id
        if not player_inputs or source_id == Consts.EMPTY_ID:
            return

        spell_ids = self._state_handler.get_spells_for_player_inputs(player_inputs)
        target_id = self._state_handler.get_current_target_for_obj(source_id)
        for spell_id in spell_ids:
            self._event_handler.dispatch_upcoming_event(timestamp, source_id, spell_id, target_id)

    def _apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        self._state_handler.apply_event(timestamp, source_id, spell_id, target_id)

    def _handle_spawn(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> list[int]:
        new_obj_ids = []
        spell = self._state_handler.get_spell_def(spell_id)
        if spell and spell.spawn_child:
            for child_init_spell in spell.spawn_child:
                new_obj_id = self._game_obj_id_gen.generate_new_id()
                self._state_handler.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id, target_id)
                self._event_handler.dispatch_upcoming_event(timestamp, new_obj_id, child_init_spell, target_id)
                new_obj_ids.append(new_obj_id)
        return new_obj_ids