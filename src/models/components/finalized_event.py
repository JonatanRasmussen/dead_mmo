from typing import Tuple, NamedTuple, Optional

from src.config.consts import Consts
from .event_outcome import EventOutcome
from .game_obj import GameObj
from .spell import Spell
from .upcoming_event import UpcomingEvent


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
