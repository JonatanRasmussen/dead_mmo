from dataclasses import dataclass, field
import json

from src.settings.consts import Consts
from src.models.components import GameObj, Position
from src.models.data import Spell
from .outcome import Outcome
from .upcoming_event import UpcomingEvent

@dataclass(slots=True)
class FinalizedEvent:
    event_id: int = Consts.EMPTY_ID
    upcoming_event: UpcomingEvent = field(default_factory=UpcomingEvent)
    source: GameObj = field(default_factory=GameObj)
    spell: Spell = field(default_factory=Spell)
    target: GameObj = field(default_factory=GameObj)
    outcome: Outcome = Outcome.EMPTY

    @classmethod
    def deserialize(cls, data: str) -> 'FinalizedEvent':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            event_id=d["eid"],
            upcoming_event=UpcomingEvent.deserialize(d["ue"]),
            source=GameObj.deserialize(d["src"]),
            spell=Spell.deserialize(d["spl"]),
            target=GameObj.deserialize(d["tgt"]),
            outcome=Outcome(d["out"])
        )
    def serialize(self) -> str:
        return json.dumps({
            "eid": self.event_id,
            "ue": json.loads(self.upcoming_event.serialize()),
            "src": json.loads(self.source.serialize()),
            "spl": json.loads(self.spell.serialize()),
            "tgt": json.loads(self.target.serialize()),
            "out": self.outcome.value
        })

    @property
    def timestamp(self) -> int:
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
    def effect_position(self) -> Position:
        """Get the position where effects should be displayed"""
        if self.spell.animate_on_target:
            game_obj = self.target
        else:
            game_obj = self.source
        return (game_obj.pos)
