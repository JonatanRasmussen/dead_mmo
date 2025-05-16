import heapq
from typing import Dict, List, Tuple, ValuesView

from src.models.aura import Aura
from src.models.combat_event import CombatEvent, FinalizedEvent
from src.handlers.id_gen import IdGen
from src.controller.read_only_world_state import ReadOnlyWorldState


class FrameEvents:

    @staticmethod
    def create_events_happening_this_frame(state: ReadOnlyWorldState) -> List[CombatEvent]:
        events_this_frame: List[CombatEvent] = []

        # Add setup event if state is not initialized
        if IdGen.is_empty_id(state.game_objs.player_id):
            setup_event = CombatEvent(
                event_id=state.event_id_gen.generate_new_id(),
                timestamp=0.0,
                source=state.game_objs.environment_id,
                spell=state.game_objs.setup_spell_id,
            )
            events_this_frame.append(setup_event)

        # Add events from periodic auras ticking this frame
        for aura in state.auras.view_auras:
            aura_tick_events = FrameEvents.create_periodic_events_this_frame(aura, state.prev_t, state.curr_t, state.event_id_gen)
            events_this_frame.extend(aura_tick_events)

        # Add events from controls (game inputs) happening this frame
        controls_events = FrameEvents._create_controls_events(state)
        events_this_frame.extend(controls_events)

        return events_this_frame

    @staticmethod
    def create_periodic_events_this_frame(aura: Aura, prev_t: float, curr_t: float, event_id_gen: IdGen) -> List[CombatEvent]:
        events: List[CombatEvent] = []
        tick_timestamps = aura.get_timestamps_for_ticks_this_frame(prev_t, curr_t)
        for timestamp in tick_timestamps:
            aura_tick = CombatEvent(
                event_id=event_id_gen.generate_new_id(),
                timestamp=timestamp,
                source=aura.source_id,
                spell=aura.aura_effect_id,
                target=aura.target_id,
                is_periodic_tick=True,
            )
            events.append(aura_tick)
        return events


    @staticmethod
    def _create_controls_events(state: ReadOnlyWorldState) -> List[CombatEvent]:
        controls_events: List[CombatEvent] = []
        controls_this_frame = state.controls.get_controls_in_timerange(state.prev_t, state.curr_t)
        for timestamp, obj_id, controls in controls_this_frame:
            if timestamp == state.prev_t:
                continue  # Prevent double processing of controls
            source_obj = state.game_objs.get_game_obj(obj_id)
            spell_ids = source_obj.convert_controls_to_spell_ids(controls)
            for spell_id in spell_ids:
                controls_events.append(CombatEvent(
                    event_id=state.event_id_gen.generate_new_id(),
                    timestamp=timestamp,
                    source=source_obj.obj_id,
                    spell=spell_id,
                    target=source_obj.current_target,
                ))
        return controls_events
