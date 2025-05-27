from typing import Tuple, NamedTuple
import math

from src.models.spell import Spell, IdGen

class Aura(NamedTuple):
    """ The effect of a previously cast spell that periodically ticks over a time span. """
    aura_id: int = IdGen.EMPTY_ID
    source_id: int = IdGen.EMPTY_ID
    origin_spell_id: int = IdGen.EMPTY_ID
    periodic_spell_id: int = IdGen.EMPTY_ID
    target_id: int = IdGen.EMPTY_ID
    start_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    is_debuff: bool = False
    is_hidden: bool = False

    @property
    def aura_key(self) -> Tuple[int, int, int]:
        return Aura.create_aura_key(self.source_id, self.origin_spell_id, self.target_id)

    @property
    def tick_interval(self) -> float:
        if self.ticks == 0 or self.duration == 0:
            return float('inf')
        return self.duration / self.ticks

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

    @staticmethod
    def create_aura_key(source_id: int, spell_id: int, target_id: int) -> Tuple[int, int, int]:
        return (source_id, spell_id, target_id)

    def is_expired(self, current_time: float) -> bool:
        return current_time > self.end_time

    def get_timestamps_for_ticks_this_frame(self, frame_start: float, frame_end: float) -> Tuple[float, ...]:
        """ Get timestamp for ticks happening this frame, excluding frame_start, including frame_end """
        start_ticks = self._ticks_elapsed(max(frame_start, self.start_time))
        end_ticks = self._ticks_elapsed(min(frame_end, self.end_time))
        return tuple(self.start_time + (tick_number * self.tick_interval) for tick_number in range(start_ticks + 1, end_ticks + 1))

    def _ticks_elapsed(self, current_time: float) -> int:
        return max(0, math.floor((current_time - self.start_time) / self.tick_interval))

    def _ticks_remaining(self, current_time: float) -> int:
        return max(0, self.ticks - self._ticks_elapsed(current_time))

    def _next_tick(self, current_time: float) -> float:
        if self._ticks_remaining(current_time) == 0:
            return float('inf')
        return self.start_time + ((self._ticks_elapsed(current_time) + 1) * self.tick_interval)