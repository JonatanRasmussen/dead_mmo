from typing import Iterable

from src.settings import Consts, HardwareInputConsts
from src.world_state.spell_registry.spell_registry import SpellRegistry
from .event_handler import EventHandler
from .state_updater import StateUpdater, DisplayObj


class WorldState:

    def __init__(self) -> None:
        self._event_handler: EventHandler = EventHandler()
        self._state_updater: StateUpdater = StateUpdater()
        self._spell_registry: SpellRegistry = WorldState._initialize_spells(self._state_updater)

    def get_display_obj_dct(self, current_time: int) -> dict[int, DisplayObj]:
        display_obj_dct: dict[int, DisplayObj] = {}
        obj_ids = self._state_updater.active_obj_ids
        for obj_id in obj_ids:
            display_obj = self._state_updater.create_display_obj(current_time, obj_id)
            display_obj.sprite_name = self._spell_registry.get_asset_name(display_obj.sprite_id)
            display_obj.audio_name = self._spell_registry.get_asset_name(display_obj.audio_id)
            display_obj_dct[obj_id] = display_obj
        return display_obj_dct

    def get_combat_interactions_for_frame(self, current_frame_time: int) -> list[tuple[int, int, int]]:
        return self._event_handler.get_combat_interactions_for_frame(current_frame_time)

    def register_player(self, timestamp: int, setup_spell_name: str) -> int:
        source_id = Consts.EMPTY_OBJ_ID
        spell_id = self._spell_registry.get_spell_id(setup_spell_name)
        dest_id = Consts.EMPTY_OBJ_ID
        player_obj_id = self._handle_event(timestamp, source_id, spell_id, dest_id)
        return player_obj_id

    def insert_player_inputs(self, player_obj_id: int, player_inputs: list[str], timestamp: int) -> None:
        for spell_name in player_inputs:
            spell_id = self._spell_registry.get_spell_id(spell_name)
            for dest_id in self._get_dests(player_obj_id, spell_id):
                self._event_handler.dispatch_upcoming_event(timestamp, player_obj_id, spell_id, dest_id)

    def process_frame(self, frame_end: int) -> None:
        while self._event_handler.has_unprocessed_events(frame_end):
            timestamp, source_id, spell_id, dest_id = self._event_handler.fetch_next_event()
            assert timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {timestamp}."
            spell_validations = self._spell_registry.get_validations(spell_id)
            validation_code = self._state_updater.validate_event(timestamp, source_id, spell_validations, dest_id)
            outcome_is_valid = self._event_handler.finalize_event(validation_code)
            if outcome_is_valid:
                self._handle_event(timestamp, source_id, spell_id, dest_id)
        self._event_handler.finalize_event_log_for_current_frame(frame_end)

    def _handle_event(self, timestamp: int, source_id: int, spell_id: int, dest_id: int) -> int:
        if self._spell_registry.is_spell_spawning_as_child(spell_id):
            new_obj_id = self._state_updater.spawn_game_obj(timestamp, source_id, spell_id, dest_id)
            new_source_id = new_obj_id
            new_dest_id = new_obj_id
        else:
            new_obj_id = Consts.EMPTY_OBJ_ID
            new_source_id = source_id
            new_dest_id = dest_id
        spell_effects = self._spell_registry.get_effects(spell_id)
        triggered_spell_ids = self._state_updater.apply_event(timestamp, spell_effects, new_dest_id)
        self._create_triggered_events(timestamp, new_dest_id, triggered_spell_ids)
        self._create_cascading_events(timestamp, new_source_id, spell_id)
        return new_obj_id

    def _create_triggered_events(self, timestamp: int, triggered_obj_id: int, triggered_spell_ids: list[int]) -> None:
        for t_spell in triggered_spell_ids:
            for dest_id in self._get_dests(triggered_obj_id, t_spell):
                self._event_handler.dispatch_upcoming_event(timestamp, triggered_obj_id, t_spell, dest_id)

    def _create_cascading_events(self, timestamp: int, source_id: int, spell_id: int) -> None:
        timeline = self._spell_registry.get_timeline_for_spell(spell_id)
        if len(timeline) > 0:
            for trigger_timestamp, timeline_spell_ids in timeline.items():
                for t_spell in timeline_spell_ids:
                    timestamp_to_use = timestamp + trigger_timestamp
                    for dest_id in self._get_dests(source_id, t_spell):
                        self._event_handler.dispatch_upcoming_event(timestamp_to_use, source_id, t_spell, dest_id)

    def _get_dests(self, source_id: int, spell_id: int) -> Iterable[int]:
        if self._spell_registry.is_spell_targeting_self(spell_id):
            yield source_id
        elif self._spell_registry.is_spell_targeting_target(spell_id):
            yield self._state_updater.get_target_for_obj(source_id)
        else:
            yield from self._state_updater.active_obj_ids

    @staticmethod
    def _initialize_spells(state_updater: StateUpdater) -> SpellRegistry:
        known_effect_types = state_updater.get_effects_known_to_systems()
        known_validation_types = state_updater.get_validations_known_to_systems()
        return SpellRegistry.initialize_with_loaded_spells(known_effect_types, known_validation_types)