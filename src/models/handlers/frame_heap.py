import heapq
from typing import List, Tuple

from src.config import Consts
from src.models.components import UpcomingEvent


class FrameHeap:
    def __init__(self) -> None:
        self._event_heap: list[tuple[int, int, int, int, int, UpcomingEvent]] = []
        self._iterations_remaining = Consts.EVENT_HEAP_MAX_ITERATIONS

    @classmethod
    def create_heap_from_list_of_events(cls, events: list[UpcomingEvent]) -> 'FrameHeap':
        event_heap = FrameHeap()
        for event in events:
            event_heap.insert_event(event)
        return event_heap

    @property
    def has_unprocessed_events(self) -> int:
        return len(self._event_heap) > 0

    def insert_event(self, event: UpcomingEvent) -> None:
        heapq.heappush(self._event_heap, (*event.key, event))
        # If two events have identical keys (should be impossible), we get '>' TypeError

    def pop_next_event(self) -> UpcomingEvent:
        assert self._iterations_remaining > 0, f"Event limit of {Consts.EVENT_HEAP_MAX_ITERATIONS} reached."
        self._iterations_remaining -= 1
        _, _, _, _, _, event = heapq.heappop(self._event_heap)
        return event