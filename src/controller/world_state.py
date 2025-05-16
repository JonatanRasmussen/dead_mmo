from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.models.aura import Aura
from src.models.combat_event import CombatEvent, FinalizedEvent
from src.handlers.aura_handler import AuraHandler
from src.handlers.controls_handler import ControlsHandler
from src.handlers.game_obj_handler import GameObjHandler
from src.handlers.event_heap import EventHeap
from src.handlers.event_log import EventLog
from src.config.spell_db import SpellDatabase
from src.controller.read_only_world_state import ReadOnlyWorldState
from src.utils.frame_events import FrameEvents
from src.utils.spell_handler import SpellHandler
from src.utils.spell_validator import SpellValidator


class WorldState:
    """ The entire game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self._previous_timestamp: float = 0.0
        self._current_timestamp: float = 0.0

        self._auras: AuraHandler = AuraHandler()
        self._controls: ControlsHandler = ControlsHandler()
        self._game_objs: GameObjHandler = GameObjHandler()
        self._spell_database: SpellDatabase = SpellDatabase()
        self._event_log: EventLog = EventLog()

    @property
    def create_readonly_view(self) -> ReadOnlyWorldState:
        return ReadOnlyWorldState(
            self._event_id_gen,
            self._previous_timestamp,
            self._current_timestamp,
            self._auras,
            self._controls,
            self._game_objs,
            self._spell_database,
            self._event_log,
        )

    @property
    def delta_time(self) -> float:
        return self._current_timestamp - self._previous_timestamp

    @property
    def all_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.view_game_objs

    def initialize_environment(self, setup_spell_id: int) -> None:
        self._game_objs.initialize_root_environment_obj(setup_spell_id)

    def process_frame(self, delta_time: float, player_input: Controls) -> None:
        self._advance_timestamp(delta_time)
        self._add_realtime_player_input(player_input)
        events_this_frame = FrameEvents.create_events_happening_this_frame(self.create_readonly_view)
        event_heap = EventHeap.create_heap_from_list_of_events(events_this_frame)
        while event_heap.has_unprocessed_events:
            event = event_heap.get_next_event()
            finalized_event = self._finalize_event(event)
            if finalized_event.outcome_is_valid:
                self._let_event_modify_world_state(finalized_event)
                if finalized_event.spell.has_cascading_events:
                    cascading_events = self._create_cascading_events(finalized_event)
                    event_heap.register_events(cascading_events)
            self._event_log.log_event(finalized_event.combat_event)

    def _advance_timestamp(self, delta_time: float) -> None:
        self._previous_timestamp = self._current_timestamp
        self._current_timestamp += delta_time

    def _add_realtime_player_input(self, player_input: Controls) -> None:
        timestamped_controls = player_input.replace_timestamp(self._current_timestamp)
        if IdGen.is_valid_id(self._game_objs.player_id):
            self._controls.add_controls(self._game_objs.player_id, self._current_timestamp, timestamped_controls)

    def _let_event_modify_world_state(self, f_event: FinalizedEvent) -> None:
        if f_event.spell.has_spawned_object:
            self._game_objs.handle_spawn(f_event.source, f_event.spell, self._controls)
        if f_event.spell.is_aura:
            self._auras.add_aura(f_event.timestamp, f_event.source_id, f_event.spell, f_event.target_id)
        updated_source_obj = SpellHandler.modify_source(f_event.timestamp, f_event.source, f_event.spell)
        self._game_objs.update_game_obj(updated_source_obj)
        updated_target_obj = SpellHandler.modify_target(updated_source_obj, f_event.spell, f_event.target, self.delta_time, self._game_objs.player_id, self._game_objs.boss1_id, self._game_objs.boss2_id)
        self._game_objs.update_game_obj(updated_target_obj)

    def _create_cascading_events(self, f_event: FinalizedEvent) -> List[CombatEvent]:
        cascading_events: List[CombatEvent] = []

        # If the event's spell cascades into new spells, add those as new events
        if f_event.spell.spell_sequence is not None:
            for next_spell in f_event.spell.spell_sequence:
                new_event = f_event.combat_event.continue_spell_sequence(self._event_id_gen.generate_new_id(), next_spell)
                cascading_events.append(new_event)

        # If an aura was just created, see if it has any ticks happening this frame
        if f_event.spell.is_aura:
            aura = self._auras.get_aura(f_event.source_id, f_event.spell_id, f_event.target_id)
            prev_t, curr_t = self._previous_timestamp, self._current_timestamp
            aura_tick_events = FrameEvents.create_periodic_events_this_frame(aura, prev_t, curr_t, self._event_id_gen)
            cascading_events.extend(aura_tick_events)

        return cascading_events

    def _finalize_event(self, event: CombatEvent) -> FinalizedEvent:
        # Convert source_id/spell_id/target_id to actual object references
        source_obj = self._game_objs.get_game_obj(event.source)
        spell = self._spell_database.get_spell(event.spell)
        target_obj = SpellHandler.select_target(source_obj, spell, event.target, self._game_objs)
        updated_event = event.update_target(target_obj.obj_id)
        outcome = SpellValidator.decide_outcome(source_obj, spell, target_obj)
        finalized_event = FinalizedEvent(
            source=source_obj,
            spell=spell,
            target=target_obj,
            combat_event=updated_event,
            outcome=outcome,
        )
        return finalized_event