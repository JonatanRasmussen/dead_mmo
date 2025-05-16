from typing import Tuple, NamedTuple
import math

from src.handlers.id_gen import IdGen
from src.models.spell import Spell


class Aura(NamedTuple):
    """ The effect of a previously cast spell that periodically ticks over a time span. """
    source_id: int = IdGen.EMPTY_ID
    spell_id: int = IdGen.EMPTY_ID
    target_id: int = IdGen.EMPTY_ID
    aura_effect_id: int = IdGen.EMPTY_ID
    start_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1
    is_debuff: bool = False
    is_hidden: bool = False

    @property
    def aura_id(self) -> Tuple[int, int, int]:
        return self.source_id, self.spell_id, self.target_id

    @property
    def tick_interval(self) -> float:
        if self.ticks == 0 or self.duration == 0:
            return float('inf')
        return self.duration / self.ticks

    @property
    def end_time(self) -> float:
        return self.start_time + self.duration

    @classmethod
    def create_from_spell(cls, timestamp: float, source_id: int, spell: Spell, target_id: int) -> 'Aura':
        return Aura(
            source_id=source_id,
            spell_id=spell.spell_id,
            target_id=target_id,
            aura_effect_id=spell.aura_effect_id,
            start_time=timestamp,
            duration=spell.duration,
            ticks=spell.ticks,
        )

    def is_expired(self, current_time: float) -> bool:
        return current_time > self.end_time

    def ticks_elapsed(self, current_time: float) -> int:
        return max(0, math.floor((current_time - self.start_time) / self.tick_interval))

    def ticks_remaining(self, current_time: float) -> int:
        return max(0, self.ticks - self.ticks_elapsed(current_time))

    def next_tick(self, current_time: float) -> float:
        if self.ticks_remaining(current_time) == 0:
            return float('inf')
        return self.start_time + ((self.ticks_elapsed(current_time) + 1) * self.tick_interval)

    def get_timestamps_for_ticks_this_frame(self, frame_start: float, frame_end: float) -> Tuple[float, ...]:
        """ Get timestamp for ticks happening this frame, excluding t=start, including t=end. """ #Note to self: Is this actually correct?
        start_ticks = self.ticks_elapsed(max(frame_start, self.start_time))
        end_ticks = self.ticks_elapsed(min(frame_end, self.end_time))
        return tuple(self.start_time + (tick_number * self.tick_interval) for tick_number in range(start_ticks + 1, end_ticks + 1))
