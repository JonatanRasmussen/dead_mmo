from typing import Tuple, NamedTuple, Iterable
import math

from src.config import Consts
from .upcoming_event import UpcomingEvent


class Aura(NamedTuple):
    """ The effect of a previously cast spell that periodically ticks over a time span. """
    aura_id: int = Consts.EMPTY_ID
    source_id: int = Consts.EMPTY_ID
    origin_spell_id: int = Consts.EMPTY_ID
    periodic_spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID
    start_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1

    @property
    def get_key_for_aura(self) -> Tuple[int, int, int]:
        return (self.source_id, self.origin_spell_id, self.target_id)

    @property
    def _tick_interval(self) -> float:
        if self.ticks == 0 or self.duration == 0:
            return float('inf')
        return self.duration / self.ticks

    @property
    def _end_time(self) -> float:
        return self.start_time + self.duration

    @property
    def _get_timestamps_for_ticks(self) -> Iterable[float]:
        """Return timestamps for all ticks occuring during the aura's lifetime. """
        if self._tick_interval == float('inf') or self.ticks <= 0:
            return
        for i in range(1, self.ticks + 1):
            yield self.start_time + i * self._tick_interval

    def create_aura_tick_events(self, frame_start: float, frame_end: float) -> Iterable[UpcomingEvent]:
        """ Return an event for each tick happening this frame, excluding frame_start, including frame_end """
        tick_timestamps = self._get_timestamps_for_ticks
        tick_event_order = 0
        for tick_timestamp in tick_timestamps:
            if frame_start < tick_timestamp <= frame_end:
                tick_event_order += 1
                yield UpcomingEvent(
                    timestamp=tick_timestamp,
                    source_id=self.source_id,
                    spell_id=self.periodic_spell_id,
                    target_id=self.target_id,
                    priority=tick_event_order,
                    aura_origin_spell_id=self.origin_spell_id,
                    aura_id=self.aura_id,
                )

    def is_expired(self, current_time: float) -> bool:
        return current_time > self._end_time

    def _ticks_elapsed(self, current_time: float) -> int:
        return max(0, math.floor((current_time - self.start_time) / self._tick_interval))

    def _ticks_remaining(self, current_time: float) -> int:
        return max(0, self.ticks - self._ticks_elapsed(current_time))

    def _next_tick(self, current_time: float) -> float:
        if self._ticks_remaining(current_time) == 0:
            return float('inf')
        return self.start_time + ((self._ticks_elapsed(current_time) + 1) * self._tick_interval)