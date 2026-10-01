from dataclasses import dataclass

from src.settings import Consts
from .event_handler import EventHandler, IdGen
from .state_handler import StateHandler, DisplayObj


class WorldState:

    ROOT_CONTROLLER_ID: int = 1

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

    def register_player(self, ingame_time: int, setup_spell_id: int) -> int:
        player_obj_id = self._game_obj_id_gen.generate_new_id()
        self._state_handler.spawn_game_obj(player_obj_id, ingame_time, player_obj_id, setup_spell_id, player_obj_id)
        self._event_handler.dispatch_upcoming_event(ingame_time, player_obj_id, setup_spell_id, player_obj_id)
        player_inputs: list[str] = []
        self.process_frame(player_obj_id, player_inputs, ingame_time)
        return player_obj_id

    def process_frame(self, player_obj_id: int, player_inputs: list[str], frame_end: int) -> None:
        spell_ids = self._state_handler.get_spells_for_player_inputs(player_obj_id, player_inputs)
        for spell_id in spell_ids:
            self._event_handler.dispatch_upcoming_event(frame_end, player_obj_id, spell_id, player_obj_id)
        while self._event_handler.has_unprocessed_events(frame_end):
            timestamp, source_id, spell_id, target_id = self._event_handler.fetch_next_event()
            assert timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {timestamp}."
            validation_code = self._state_handler.validate_event(timestamp, source_id, spell_id, target_id)
            outcome_is_valid = self._event_handler.finalize_event(validation_code)
            if outcome_is_valid:
                self._handle_spawn(timestamp, source_id, spell_id, target_id)
                self._state_handler.apply_event(timestamp, spell_id, target_id)
                self._create_cascading_events(timestamp, source_id, spell_id)
        self._event_handler.finalize_event_log_for_current_frame(frame_end)

    def _create_cascading_events(self, timestamp: int, source_id: int, spell_id: int) -> None:
        """
        for cascaded_spell_id in self._state_handler.get_cascades(spell_id):
            delay = self._state_handler.get_spell_delay(cascaded_spell_id)
            new_timestamp = timestamp + delay
            if self._state_handler.is_spell_selfcast(cascaded_spell_id):
                target_ids = {1}
            else:
                assert delay == 0, f"Unsupported spell config for {cascaded_spell_id}: AoE spells cannot be delayed."
                target_ids = self._state_handler.get_aoe_targets(source_id, cascaded_spell_id)
            for target_id in target_ids:
                if self._state_handler.is_spell_spawning_as_child(cascaded_spell_id):
                    assert delay == 0, f"Unsupported spell config for {cascaded_spell_id}: Child spells cannot be delayed."
                    new_source_id = self._game_obj_id_gen.generate_new_id()
                    self._state_handler.spawn_game_obj(new_source_id, timestamp, source_id, spell_id, target_id)
                else:
                    new_source_id = source_id
                self._event_handler.dispatch_upcoming_event(new_timestamp, new_source_id, cascaded_spell_id, target_id)
        """

        timeline = self._state_handler.get_timeline_for_spell(spell_id)
        if len(timeline) > 0:
            #target_id = self._state_handler.get_current_target_for_obj(source_id)
            for trigger_timestamp, timeline_spell_ids in timeline.items():
                for t_spell in timeline_spell_ids:
                    new_timestamp = timestamp + trigger_timestamp
                    #new_timestamp = timestamp + self._state_handler.get_spell_delay(t_spell)
                    self._event_handler.dispatch_upcoming_event(new_timestamp, source_id, t_spell, source_id)

        aoe_spell_id = self._state_handler.get_aoe_spell_id(spell_id)
        if aoe_spell_id != Consts.EMPTY_SPELL_ID:
            # For now, try hit everything and let event validation fail on undesired aoe targets
            target_ids = self._state_handler.get_aoe_targets(source_id, aoe_spell_id)  # We can optimize later on
            for target_id in target_ids:
                self._event_handler.dispatch_upcoming_event(timestamp, source_id, aoe_spell_id, target_id)

        signal_spell_id = self._state_handler.get_signal_spell_id(spell_id)
        if signal_spell_id != Consts.EMPTY_SPELL_ID:
            signalled_obj_ids = self._state_handler.get_signalled_objs(source_id, aoe_spell_id)  # We can optimize later on
            for signalled_obj_id in signalled_obj_ids:
                self._event_handler.dispatch_upcoming_event(timestamp, signalled_obj_id, signal_spell_id, signalled_obj_id)

    def _handle_spawn(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        child_init_spell_ids = self._state_handler.get_spawn_child_id(spell_id)
        for child_init_spell in child_init_spell_ids:
            new_obj_id = self._game_obj_id_gen.generate_new_id()
            self._state_handler.spawn_game_obj(new_obj_id, timestamp, source_id, spell_id, target_id)
            self._event_handler.dispatch_upcoming_event(timestamp, new_obj_id, child_init_spell, new_obj_id)