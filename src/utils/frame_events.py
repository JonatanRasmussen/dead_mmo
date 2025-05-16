import heapq
from typing import Dict, List, Tuple, ValuesView

from src.models.aura import Aura
from src.models.combat_event import CombatEvent, FinalizedEvent
from src.models.important_ids import ImportantIDs
from src.handlers.id_gen import IdGen
from src.controller.world_state import WorldState


class FrameEvents:

    @staticmethod
    def create_events_happening_this_frame(state: WorldState) -> List[CombatEvent]:
        events_this_frame: List[CombatEvent] = []

        # Add setup event if state is not initialized
        if IdGen.is_empty_id(state.important_ids.player_id):
            setup_event = CombatEvent(
                event_id=state.generate_new_event_id(),
                timestamp=0.0,
                source=state.important_ids.environment_id,
                spell=state.important_ids.setup_spell_id,
            )
            events_this_frame.append(setup_event)

        # Add events from periodic auras ticking this frame
        for aura in state.view_auras:
            aura_tick_events = FrameEvents.create_periodic_events_this_frame(aura, state)
            events_this_frame.extend(aura_tick_events)

        # Add events from controls (game inputs) happening this frame
        controls_events = FrameEvents._create_controls_events(state)
        events_this_frame.extend(controls_events)

        return events_this_frame

    @staticmethod
    def create_periodic_events_this_frame(aura: Aura, state: WorldState) -> List[CombatEvent]:
        events: List[CombatEvent] = []
        prev_t, curr_t = state.timestamps
        tick_timestamps = aura.get_timestamps_for_ticks_this_frame(prev_t, curr_t)
        for timestamp in tick_timestamps:
            aura_tick = CombatEvent(
                event_id=state.generate_new_event_id(),
                timestamp=timestamp,
                source=aura.source_id,
                spell=aura.aura_effect_id,
                target=aura.target_id,
                is_periodic_tick=True,
            )
            events.append(aura_tick)
        return events


    @staticmethod
    def _create_controls_events(state: WorldState) -> List[CombatEvent]:
        controls_events: List[CombatEvent] = []
        controls_this_frame = state.view_controls_for_current_frame
        _, current_timestamp = state.timestamps
        for timestamp, obj_id, controls in controls_this_frame:
            if timestamp == current_timestamp:
                continue  # Prevent double processing of controls
            source_obj = state.get_game_obj(obj_id)
            spell_ids = source_obj.convert_controls_to_spell_ids(controls)
            for spell_id in spell_ids:
                controls_events.append(CombatEvent(
                    event_id=state.generate_new_event_id(),
                    timestamp=timestamp,
                    source=source_obj.obj_id,
                    spell=spell_id,
                    target=source_obj.current_target,
                ))
        return controls_events