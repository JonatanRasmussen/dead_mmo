import heapq
from typing import Dict, List, Tuple, ValuesView

from src.models.combat_event import CombatEvent, FinalizedEvent


class EventHeap:
    MAX_ITERATIONS = 100_000

    def __init__(self) -> None:
        self._event_heap: List[Tuple[float, int, int, CombatEvent]] = []
        self._iterations_remaining = EventHeap.MAX_ITERATIONS

    @classmethod
    def create_heap_from_list_of_events(cls, events: List[CombatEvent]) -> 'EventHeap':
        event_heap = EventHeap()
        event_heap.register_events(events)
        return event_heap

    @property
    def has_unprocessed_events(self) -> float:
        return len(self._event_heap) > 0

    def get_next_event(self) -> CombatEvent:
        assert self._iterations_remaining > 0, f"Event limit of {EventHeap.MAX_ITERATIONS} reached."
        self._iterations_remaining -= 1
        _, _, _, event = heapq.heappop(self._event_heap)
        return event

    def register_event(self, event: CombatEvent) -> None:
        heapq.heappush(self._event_heap, (event.timestamp, event.source, event.event_id, event))

    def register_events(self, events: List[CombatEvent]) -> None:
        for event in events:
            self.register_event(event)
