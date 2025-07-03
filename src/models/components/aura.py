from typing import Iterable
from dataclasses import dataclass

from src.config import Consts

@dataclass(slots=True)
class Aura:
    """ The effect of a previously cast spell that periodically ticks over a time span. """
    source_id: int = Consts.EMPTY_ID  # game_obj source
    target_id: int = Consts.EMPTY_ID  # game_obj target
    origin_spell_id: int = Consts.EMPTY_ID  # spell that applied aura
    periodic_spell_id: int = Consts.EMPTY_ID  # spell to be cast each tick
    start_time: float = 0.0
    duration: float = 0.0
    ticks: int = 1

    @property
    def key(self) -> tuple[int, int, int]:
        return (self.source_id, self.origin_spell_id, self.target_id)

    @property
    def tick_timestamps(self) -> Iterable[float]:
        """Return timestamps for all ticks occuring during the aura's lifetime. """
        if self.ticks > 0:
            tick_interval = self.duration / self.ticks
            for i in range(1, self.ticks + 1):
                yield self.start_time + i * tick_interval

    def is_expired(self, current_time: float) -> bool:
        end_time = self.start_time + self.duration
        return current_time > end_time

    def ticks_remaining(self, current_time: float) -> int:
        return sum(1 for t in self.tick_timestamps if t > current_time)