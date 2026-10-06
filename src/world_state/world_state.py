from typing import Iterable

from src.settings import Consts, HardwareInputConsts
from src.world_state.spell_handler.spell_handler import SpellHandler
from .event_handler import EventHandler, IdGen
from .state_handler import StateHandler, DisplayObj


class WorldState:

    def __init__(self) -> None:
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._event_handler: EventHandler = EventHandler()
        self._state_handler: StateHandler = StateHandler()
        self._spell_handler: SpellHandler = SpellHandler.initialize_with_loaded_spells(self._state_handler.get_valid_effects(), self._state_handler.get_valid_validations())

    def get_display_obj_dct(self, current_time: int) -> dict[int, DisplayObj]:
        display_obj_dct: dict[int, DisplayObj] = {}
        obj_ids = self._state_handler.active_obj_ids
        for obj_id in obj_ids:
            display_obj = self._state_handler.create_display_obj(current_time, obj_id)
            display_obj.sprite_name = self._spell_handler.get_asset_name(display_obj.sprite_id)
            display_obj.audio_name = self._spell_handler.get_asset_name(display_obj.audio_id)
            display_obj_dct[obj_id] = display_obj
        return display_obj_dct

    def get_combat_interactions_for_frame(self, current_frame_time: int) -> list[tuple[int, int, int]]:
        return self._event_handler.get_combat_interactions_for_frame(current_frame_time)

    def register_player(self, ingame_time: int, setup_spell_name: str) -> int:
        setup_spell_id = self._spell_handler.get_spell_id(setup_spell_name)
        new_obj_id = self._handle_event(ingame_time, Consts.EMPTY_OBJ_ID, setup_spell_id, Consts.EMPTY_OBJ_ID)
        player_inputs: list[str] = []
        self.process_frame(new_obj_id, player_inputs, ingame_time)
        return new_obj_id

    def process_frame(self, player_obj_id: int, player_inputs: list[str], frame_end: int) -> None:
        spell_names = HardwareInputConsts.get_spell_names_for_player_inputs(player_obj_id, player_inputs)
        for spell_name in spell_names:
            spell_id = self._spell_handler.get_spell_id(spell_name)
            self._event_handler.dispatch_upcoming_event(frame_end, player_obj_id, spell_id, player_obj_id)

        while self._event_handler.has_unprocessed_events(frame_end):
            timestamp, source_id, spell_id, target_id = self._event_handler.fetch_next_event()
            assert timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {timestamp}."
            spell_validations = self._spell_handler.get_validations(spell_id)
            validation_code = self._state_handler.validate_event(timestamp, source_id, spell_validations, target_id)
            outcome_is_valid = self._event_handler.finalize_event(validation_code)
            if outcome_is_valid:
                self._handle_event(timestamp, source_id, spell_id, target_id)
        self._event_handler.finalize_event_log_for_current_frame(frame_end)

    def _handle_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        new_obj_id = self._handle_spawn(timestamp, source_id, spell_id, target_id)
        source_to_use = new_obj_id if new_obj_id != Consts.EMPTY_OBJ_ID else source_id
        target_to_use = new_obj_id if new_obj_id != Consts.EMPTY_OBJ_ID else target_id
        spell_effects = self._spell_handler.get_effects(spell_id)
        triggered_spell_ids = self._state_handler.apply_event(timestamp, spell_effects, target_to_use)
        self._create_triggered_events(timestamp, target_to_use, triggered_spell_ids)
        self._create_cascading_events(timestamp, source_to_use, spell_id)
        return new_obj_id

    def _create_triggered_events(self, timestamp: int, triggered_obj_id: int, triggered_spell_ids: list[int]) -> None:
        for t_spell in triggered_spell_ids:
            for target_id in self._get_targets(triggered_obj_id, t_spell):
                self._event_handler.dispatch_upcoming_event(timestamp, triggered_obj_id, t_spell, target_id)

    def _create_cascading_events(self, timestamp: int, source_id: int, spell_id: int) -> None:
        timeline = self._spell_handler.get_timeline_for_spell(spell_id)
        if len(timeline) > 0:
            #target_id = self._state_handler.get_current_target_for_obj(source_id)
            for trigger_timestamp, timeline_spell_ids in timeline.items():
                for t_spell in timeline_spell_ids:
                    timestamp_to_use = timestamp + trigger_timestamp
                    for target_id in self._get_targets(source_id, t_spell):
                        self._event_handler.dispatch_upcoming_event(timestamp_to_use, source_id, t_spell, target_id)

    def _get_targets(self, source_id: int, spell_id: int) -> Iterable[int]:
        if self._spell_handler.is_spell_targeting_self(spell_id):
            yield source_id
        elif self._spell_handler.is_spell_targeting_destination(spell_id):
            yield self._state_handler.get_destination_for_obj(source_id)
        else:
            yield from self._state_handler.active_obj_ids

    def _handle_spawn(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        if self._spell_handler.is_spell_spawning_as_child(spell_id):
            new_source_id = self._game_obj_id_gen.generate_new_id()
            self._state_handler.spawn_game_obj(new_source_id, timestamp, source_id, spell_id, target_id)
            return new_source_id
        return Consts.EMPTY_OBJ_ID