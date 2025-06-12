from typing import Tuple, NamedTuple, Optional
from enum import Enum, auto

from src.config.consts import Consts
from .game_obj import GameObj
from .spell import SpellFlag, Spell, GameObjStatus
from .upcoming_event import UpcomingEvent


class EventOutcome(Enum):
    EMPTY = 0
    SUCCESS = auto()
    OUT_OF_RANGE = auto()
    GCD_NOT_READY = auto()
    NO_TARGET_WAS_SELECTED = auto()
    SOURCE_IS_DISABLED = auto()
    TARGET_IS_INVALID = auto()
    AURA_NO_LONGER_EXISTS = auto()

    @property
    def is_success(self) -> bool:
        return self in {EventOutcome.SUCCESS}

    @staticmethod
    def decide_outcome(timestamp: float, source_obj: GameObj, spell: Spell, target_obj: GameObj) -> 'EventOutcome':
        if not target_obj.status.is_valid_target and not source_obj.obj_id == target_obj.obj_id:
            return EventOutcome.TARGET_IS_INVALID
        if not source_obj.status.is_valid_source:
            return EventOutcome.SOURCE_IS_DISABLED
        if not EventOutcome._is_within_range(source_obj, spell, target_obj):
            return EventOutcome.OUT_OF_RANGE
        if not EventOutcome._gcd_is_available(timestamp, source_obj, spell):
            return EventOutcome.GCD_NOT_READY
        # More outcome conditions to be added here.
        return EventOutcome.SUCCESS

    @staticmethod
    def _is_within_range(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> bool:
        if not spell.has_range_limit:
            return True
        return (source_obj.x - target_obj.x) ** 2 + (source_obj.y - target_obj.y) ** 2 <= spell.range_limit ** 2

    @staticmethod
    def _gcd_is_available(timestamp: float, source_obj: GameObj, spell: Spell) -> bool:
        if not spell.flags & SpellFlag.TRIGGER_GCD:
            return True
        return source_obj.get_gcd_progress(timestamp) >= 1.0


class FinalizedEvent(NamedTuple):
    event_id: int = Consts.EMPTY_ID
    upcoming_event: UpcomingEvent = UpcomingEvent()
    source: GameObj = GameObj()
    spell: Spell = Spell()
    target: GameObj = GameObj()
    outcome: EventOutcome = EventOutcome.EMPTY

    @property
    def timestamp(self) -> float:
        return self.upcoming_event.timestamp
    @property
    def source_id(self) -> int:
        return self.source.obj_id
    @property
    def spell_id(self) -> int:
        return self.spell.spell_id
    @property
    def target_id(self) -> int:
        return self.target.obj_id

    @property
    def outcome_is_valid(self) -> bool:
        return self.outcome.is_success

    @property
    def event_summary(self) -> str:
        return f"[{self.timestamp:.3f}: id={self.event_id:04d}] {self.outcome} (obj_{self.source_id:04d} uses spell_{self.spell_id:04d} on obj_{self.target_id:04d}.)"

    def update_source(self, new_source: GameObj) -> 'FinalizedEvent':
        return self._replace(source=new_source)

    # Audio properties
    @property
    def should_play_audio(self) -> bool:
        """Determine if this event should play audio"""
        return self.spell.should_play_audio and self.outcome_is_valid

    @property
    def audio_name(self) -> str:
        """Get the audio file name for this event"""
        return self.spell.audio_name

    # Animation properties
    @property
    def should_play_animation(self) -> bool:
        """Determine if this event should play an animation"""
        return self.spell.should_play_animation and self.outcome_is_valid

    @property
    def animation_name(self) -> str:
        """Get the animation name for this event"""
        return self.spell.animation_name

    @property
    def animation_scale(self) -> float:
        """Get the scale factor for the animation"""
        return self.spell.animation_scale

    # Additional helper properties
    @property
    def effect_position(self) -> tuple[float, float]:
        """Get the position where effects should be displayed as a tuple"""
        if self.spell.animate_on_target:
            game_obj = self.target
        else:
            game_obj = self.source
        return (game_obj.x, game_obj.y)
