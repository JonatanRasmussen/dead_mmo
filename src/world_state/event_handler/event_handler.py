from src.settings import Consts
from ._combat_event import CombatEvent
from ._event_log import EventLog
from ._frame_heap import FrameHeap
from .id_gen import IdGen


class EventHandler:
    def __init__(self) -> None:
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 100_000)
        self._event_log_for_each_frame: dict[int, EventLog] = {}
        self._event_log_for_current_frame: EventLog = EventLog()
        self._current_event: CombatEvent | None = None

    @property
    def current_events_timestamp(self) -> int:
        assert self._current_event, "The current event has been finalized."
        return self._current_event.timestamp

    @property
    def current_events_source_id(self) -> int:
        assert self._current_event, "The current event has been finalized."
        return self._current_event.source_id

    @property
    def current_events_spell_id(self) -> int:
        assert self._current_event, "The current event has been finalized."
        return self._current_event.spell_id

    @property
    def current_events_target_id(self) -> int:
        assert self._current_event, "The current event has been finalized."
        return self._current_event.target_id

    def has_unprocessed_events(self, frame_end: int) -> bool:
        return self._event_heap.has_unprocessed_events(frame_end)

    def fetch_next_event(self) -> None:
        assert not self._current_event, "New event was fetched before previous event was finalized."
        self._current_event = self._event_heap.pop_next_event()

    def finalize_event(self, error_msg: str) -> bool:
        assert self._current_event, "The current event has been finalized."
        finalized_event = CombatEvent(
            event_id=self._current_event.event_id,
            timestamp=self._current_event.timestamp,
            source_id=self._current_event.source_id,
            spell_id=self._current_event.spell_id,
            target_id=self._current_event.target_id,
            validation_error_msg=error_msg,
            spell_modifier=self._current_event.spell_modifier,
        )
        self._event_log_for_current_frame.log_event(finalized_event)
        self._current_event = None
        return finalized_event.outcome_is_successful

    def finalize_event_log_for_current_frame(self, current_frame_timestamp: int) -> None:
        self._event_log_for_each_frame[current_frame_timestamp] = self._event_log_for_current_frame
        self._event_log_for_current_frame = EventLog()

    def get_combat_interactions_for_frame(self, current_frame_timestamp: int) -> list[tuple[int, int, int]]:
        combat_interactions: list[tuple[int, int, int]] = []
        for evt in self._event_log_for_each_frame[current_frame_timestamp].view_all_events:
            if evt.outcome_is_successful:
                interaction = (evt.source_id, evt.spell_id, evt.target_id)
                combat_interactions.append(interaction)
        return combat_interactions

    def dispatch_upcoming_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        event_id=self._event_id_gen.generate_new_id()
        setup_event = CombatEvent(event_id, timestamp, source_id, spell_id, target_id)
        self._event_heap.insert_event(setup_event)