from typing import Iterable, ValuesView, Optional
from dataclasses import replace

from src.config import Consts
from src.models.components import Controls, EventOutcome, GameObj, DefaultIDs, UpcomingEvent, FinalizedEvent, Targeting
from src.models.handlers import AuraHandler, ControlsHandler, EventLog, FrameHeap, GameObjHandler, IdGen, SpellDatabase


class WorldState:
    """ The entire game state of the save file that is currently in use """

    def __init__(self, environment_setup_id: int) -> None:
        self._environment_setup_id: int = environment_setup_id
        self._auras: AuraHandler = AuraHandler()
        self._controls: ControlsHandler = ControlsHandler()
        self._game_objs: GameObjHandler = GameObjHandler()
        self._spell_database: SpellDatabase = SpellDatabase()

    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.view_game_objs
    @property
    def default_ids(self) -> DefaultIDs:
        return self._game_objs.default_ids
    def add_realtime_player_controls(self, player_input: Controls, frame_middle: float) -> None:
        self._controls.add_realtime_player_controls(player_input, frame_middle, self.default_ids.player_id)

    def process_frame(self, frame_start: float, frame_end: float) -> EventLog:
        event_log = EventLog(frame_start, frame_end)
        event_id_gen = IdGen.create_preassigned_range(1, 10_000)
        event_heap = FrameHeap()

        # Initialize environment if this is the very first frame
        if not self.default_ids.environment_exists:
            self._game_objs.initialize_environment()
            event_heap.insert_event(UpcomingEvent(timestamp=0.0, spell_id=self._environment_setup_id))

        # Prepare state updates for current frame
        for event in self._fetch_events_happening_this_frame(frame_start, frame_end):
            event_heap.insert_event(event)

        # Execute state updates for current frame
        while event_heap.has_unprocessed_events:
            u_event = event_heap.pop_next_event()
            assert (u_event.timestamp > frame_start or u_event.timestamp == 0.0), f"frame starts at {frame_start} but event has timestamp {u_event}."
            assert u_event.timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {u_event}."
            f_event = self._finalize_event(u_event, event_id_gen.generate_new_id())
            event_log.log_event(f_event)
            if f_event.outcome_is_valid:
                new_obj = self._game_objs.handle_spawn(f_event)
                self._controls.add_controls_for_newly_spawned_obj(new_obj, f_event.spell)
                self._auras.handle_aura(f_event)
                if f_event.spell.has_cascading_events:
                    for cascading_event in self._fetch_cascading_events(frame_start, frame_end, f_event, new_obj):
                        event_heap.insert_event(cascading_event)
                self._game_objs.modify_game_obj(f_event)

        # Finish and clean up state for upcoming frames
        self._remove_all_expired_auras(frame_end)
        return event_log

    def _fetch_events_happening_this_frame(self, frame_start: float, frame_end: float) -> Iterable[UpcomingEvent]:
        """ Create events for periodic effects and controls that are scheduled for this frame. """
        for aura in self._auras.view_auras:
            yield from UpcomingEvent.create_aura_tick_events(aura, frame_start, frame_end)
        for _, obj_id, controls in self._controls.get_controls_in_timerange(frame_start, frame_end):
            assert (controls.ingame_time > frame_start or controls.ingame_time == 0.0), f"frame starts at {frame_start} but controls has timestamp {controls.ingame_time}."
            assert controls.ingame_time <= frame_end, f"frame ends at {frame_end}, but controls has timestamp {controls.ingame_time}."
            game_obj = self._game_objs.get_game_obj(obj_id)
            yield from UpcomingEvent.create_events_from_controls(game_obj, controls, frame_start, frame_end)

    def _fetch_cascading_events(self, frame_start: float, frame_end: float, f_event: FinalizedEvent, new_obj: Optional[GameObj]) -> Iterable[UpcomingEvent]:
        # If the event's spell spawned an obj, add any new controls happening this frame
        if new_obj is not None and f_event.spell.obj_controls is not None:
            assert f_event.spell.spawned_obj is not None, "new_obj exists but is not from spell."
            for controls in f_event.spell.copy_obj_controls:
                assert (new_obj.cds.spawn_timestamp > frame_start or new_obj.cds.spawn_timestamp == 0.0), f"frame starts at {frame_start} but {new_obj.obj_id} has spawn_timestamp {new_obj.cds.spawn_timestamp}."
                assert new_obj.cds.spawn_timestamp <= frame_end, f"frame ends at {frame_end} but {new_obj.obj_id} has spawn_timestamp {new_obj.cds.spawn_timestamp}."
                controls.increase_offset(new_obj.cds.spawn_timestamp)
                assert not controls.is_empty, f"Controls for {new_obj.obj_id} is empty."
                yield from UpcomingEvent.create_events_from_controls(new_obj, controls, frame_start, frame_end)

        # If the event's spell is area-of-effect, add new events for each target
        if f_event.spell.is_area_of_effect and not f_event.upcoming_event.is_aoe_targeting:
            priority = f_event.upcoming_event.priority
            for target_id in Targeting.select_targets_for_aoe(f_event.source, f_event.target, self.view_game_objs):
                priority += 1
                aoe_copy = replace(f_event.upcoming_event)
                aoe_copy.priority = priority
                aoe_copy.target_id = target_id
                aoe_copy.is_aoe_targeting = True
                yield aoe_copy

        # If the event's spell cascades into new spells, add those as new events
        if f_event.spell.spell_sequence is not None:
            priority = f_event.upcoming_event.priority
            for next_spell in f_event.spell.spell_sequence:
                priority += 1
                sequence_copy = replace(f_event.upcoming_event)
                sequence_copy.spell_id = next_spell
                sequence_copy.priority = priority
                yield sequence_copy

        # If an aura was just created, see if it has any ticks happening this frame
        if f_event.spell.has_aura_apply:
            aura = self._auras.get_aura(f_event.source_id, f_event.spell_id, f_event.target_id)
            yield from UpcomingEvent.create_aura_tick_events(aura, frame_start, frame_end)

    def _finalize_event(self, event: UpcomingEvent, event_id: int) -> FinalizedEvent:
        # Convert source_id/spell_id/target_id to actual object references
        if Consts.is_valid_id(event.source_id):
            source_id = event.source_id
        else:
            source_id = self.default_ids.environment_id
        source_obj = self._game_objs.get_game_obj(source_id)
        spell = self._spell_database.get_spell(event.spell_id)
        if event.is_aoe_targeting:
            target_id = event.target_id
        else:
            target_id = spell.targeting.select_target(source_obj, self.default_ids)
        if target_id == source_obj.obj_id:
            target_obj = source_obj
        else:
            if spell.is_target_of_target and Consts.is_valid_id(target_id):
                obj_with_target_to_copy = self._game_objs.get_game_obj(target_id)
                if Consts.is_valid_id(obj_with_target_to_copy.current_target):
                    target_id = obj_with_target_to_copy.current_target
                else:
                    target_id = self.default_ids.missing_target_id
            target_obj = self._game_objs.get_game_obj(target_id)

        # Finalize the event's outcome and update its source and target
        if event.is_aura_tick and not self._auras.aura_exists(event):  # Do NOT use updated_event here
            outcome = EventOutcome.AURA_NO_LONGER_EXISTS
        else:
            event.source_id = source_obj.obj_id
            event.target_id = target_obj.obj_id
            outcome = EventOutcome.decide_outcome(event.timestamp, source_obj, spell, target_obj, event.is_aoe_targeting)
        finalized_event = FinalizedEvent(
            event_id=event_id,
            source=source_obj,
            spell=spell,
            target=target_obj,
            upcoming_event=event,
            outcome=outcome,
        )
        return finalized_event

    def _remove_all_expired_auras(self, frame_end: float) -> None:
        cached_source: GameObj = GameObj()
        for aura in self._auras.view_auras:
            if aura.source_id != cached_source.obj_id:
                # Because view_auras is a SortedDict, auras from the same source is in sequence
                assert aura.source_id > cached_source.obj_id
                cached_source = self._game_objs.get_game_obj(aura.source_id)
            if aura.is_expired(frame_end) or cached_source.is_despawned:
                self._auras.remove_aura(*aura.key)
