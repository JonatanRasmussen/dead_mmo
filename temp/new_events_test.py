from dataclasses import dataclass, field, asdict

@dataclass(slots=True)
class EventIntent:
    """
    A scheduled action, not yet validated against game state.
    Carries only IDs — no object references.
    Mutable until resolved.
    """
    event_id: int                        # assigned at scheduling time
    timestamp: int
    priority: int

    source_id: int
    spell_id: int
    target_id: int
    spell_modifier: float

    # Scheduling metadata — consider if these belong here or in a wrapper
    aura_key: tuple | None               # replaces aura_origin_spell_id + aura_start_time
    is_spell_sequence: bool
    is_aoe_targeting: bool


@dataclass(frozen=True, slots=True)     # frozen = immutable once created
class EventResult:
    """
    Immutable record of something that happened.
    Stores only IDs and deltas — no object references, no snapshots.
    """
    event_id: int
    timestamp: int

    source_id: int
    spell_id: int
    target_id: int
    spell_modifier: float

    outcome: bool  #replace with Outcome
    hp_delta: float                      # actual change applied, 0 if missed
    is_aura_tick: bool                   # derived from intent at resolution time


class EventLog:
    def __init__(self) -> None:
        self._log: dict[int, EventResult] = {}

    def record(self, result: EventResult) -> None:
        assert result.event_id not in self._log
        self._log[result.event_id] = result




#Your Velocity-Based Movement System
#What you are describing is called *dead reckoning* and it is a well-established pattern.
@dataclass(frozen=True, slots=True)
class MovementState:
    timestamp: int        # when this state was set
    source_id: int
    x: float
    y: float
    velocity_x: float     # units per second
    velocity_y: float     # units per second

    def position_at(self, current_time: int) -> tuple[float, float]:
        elapsed = (current_time - self.timestamp) / 1000.0
        return (
            self.x + self.velocity_x * elapsed,
            self.y + self.velocity_y * elapsed
        )