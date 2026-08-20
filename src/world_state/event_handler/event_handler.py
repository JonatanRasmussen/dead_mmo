from typing import Iterable

from src.settings import Consts
from ._combat_event import CombatEvent
from ._event_log import EventLog
from ._frame_heap import FrameHeap
from ._outcome import Outcome
from .id_gen import IdGen


class EventHandler:
    EMPTY_EVENT = CombatEvent(event_id=Consts.EMPTY_ID)
    def __init__(self) -> None:
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 100_000)
        self._event_log_for_each_frame: dict[int, EventLog] = {}
        self._event_log_for_current_frame: EventLog = EventLog()
        self._current_event: CombatEvent = EventHandler.EMPTY_EVENT

    @property
    def current_events_timestamp(self) -> int:
        return self._current_event.timestamp

    @property
    def current_events_source_id(self) -> int:
        return self._current_event.source_id

    @property
    def current_events_spell_id(self) -> int:
        return self._current_event.spell_id

    @property
    def current_events_target_id(self) -> int:
        return self._current_event.target_id

    def has_unprocessed_events(self, frame_end: int) -> bool:
        return self._event_heap.has_unprocessed_events(frame_end)

    def fetch_next_event(self) -> None:
        assert self._current_event.event_id == EventHandler.EMPTY_EVENT.event_id, "New event was fetched before previous event was finalized."
        self._current_event = self._event_heap.pop_next_event()

    def finalize_event(self, finalized_target_id: int, outcome: Outcome) -> None:
        finalized_event = CombatEvent(
            event_id=self._current_event.event_id,
            timestamp=self._current_event.timestamp,
            source_id=self._current_event.source_id,
            spell_id=self._current_event.spell_id,
            target_id=finalized_target_id,
            outcome=outcome,
        )
        self._event_log_for_current_frame.log_event(finalized_event)
        self._current_event = EventHandler.EMPTY_EVENT

    def assign_outcome_success(self, finalized_target_id: int) -> None:
        self.finalize_event(finalized_target_id, Outcome.SUCCESS)

    def assign_outcome_source_is_disabled(self, finalized_target_id: int) -> None:
        self.finalize_event(finalized_target_id, Outcome.SOURCE_IS_DISABLED)

    def assign_outcome_gcd_not_ready(self, finalized_target_id: int) -> None:
        self.finalize_event(finalized_target_id, Outcome.GCD_NOT_READY)

    def assign_outcome_invalid_target(self, finalized_target_id: int) -> None:
        self.finalize_event(finalized_target_id, Outcome.TARGET_IS_INVALID)

    def assign_outcome_out_of_range(self, finalized_target_id: int) -> None:
        self.finalize_event(finalized_target_id, Outcome.OUT_OF_RANGE)

    def finalize_event_log_for_current_frame(self, current_frame_timestamp: int) -> None:
        self._event_log_for_each_frame[current_frame_timestamp] = self._event_log_for_current_frame
        self._event_log_for_current_frame = EventLog()

    def get_successful_spell_ids(self, current_frame_timestamp: int) -> Iterable[int]:
        return self._event_log_for_each_frame[current_frame_timestamp].get_successful_spell_ids

    def dispatch_upcoming_targeted_event(self, timestamp: int, source_id: int, spell_id: int, target_id) -> None:
        event_id=self._event_id_gen.generate_new_id()
        setup_event = CombatEvent(event_id, timestamp, source_id, spell_id, target_id)
        self._event_heap.insert_event(setup_event)

    def dispatch_upcoming_untargeted_event(self, timestamp: int, source_id: int, spell_id: int) -> None:
        event_id=self._event_id_gen.generate_new_id()
        setup_event = CombatEvent(event_id, timestamp, source_id, spell_id)
        self._event_heap.insert_event(setup_event)