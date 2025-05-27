import heapq
from typing import List, Tuple

from src.models.event import UpcomingEvent


class EventHeap:
    MAX_ITERATIONS = 100_000

    def __init__(self) -> None:
        self._event_heap: List[Tuple[float, int, int, UpcomingEvent]] = []
        self._iterations_remaining = EventHeap.MAX_ITERATIONS

    @classmethod
    def create_heap_from_list_of_events(cls, events: List[UpcomingEvent]) -> 'EventHeap':
        event_heap = EventHeap()
        for event in events:
            event_heap.insert_event(event)
        return event_heap

    @property
    def has_unprocessed_events(self) -> float:
        return len(self._event_heap) > 0

    def pop_next_event(self) -> UpcomingEvent:
        assert self._iterations_remaining > 0, f"Event limit of {EventHeap.MAX_ITERATIONS} reached."
        self._iterations_remaining -= 1
        _, _, _, event = heapq.heappop(self._event_heap)
        return event

    def insert_event(self, event: UpcomingEvent) -> None:
        heapq.heappush(self._event_heap, (event.timestamp, event.source_id, event.event_id, event))
