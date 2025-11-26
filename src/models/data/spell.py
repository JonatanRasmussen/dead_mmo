from typing import Iterable, Optional
from dataclasses import dataclass
import json

from src.settings import Consts
from src.models.components import Controls, ObjTemplate
from .behavior import Behavior
from .targeting import Targeting


@dataclass(slots=True)
class Spell:
    """ An action that can be performed by a game object. """
    spell_id: int = Consts.EMPTY_ID
    effect_id: int = Consts.EMPTY_ID
    spell_sequence: Optional[tuple[int, ...]] = None

    power: float = 1.0
    variance: float = 0.0

    range_limit: float = 0.0
    #self.cost: float = 0 #not yet implemented
    #self.gcd_mod: float = 0.0 #not yet implemented
    cast_time: int = 0
    duration: int = 0
    ticks: int = 1
    #max_stacks: int = 1 #not yet implemented

    flags: Behavior = Behavior.NONE
    targeting: Targeting = Targeting.NONE

    spawned_obj: Optional[ObjTemplate] = None

    # Audio properties
    audio_name: str = ""
    spell_type: str = ""

    # Animation properties
    animation_name: str = ""
    animation_scale: float = 1.0

    # Effect placement
    animate_on_target: bool = True  # If False, animate on source

    @classmethod
    def deserialize(cls, data: str) -> 'Spell':
        d = json.loads(data) if isinstance(data, str) else data

        seq = None
        if d["seq"] is not None:
            seq = tuple(int(x) for x in d["seq"])

        spawned = (
            ObjTemplate.deserialize(d["spn"])
            if d["spn"] is not None else None
        )

        return cls(
            spell_id=d["sid"],
            effect_id=d["eid"],
            spell_sequence=seq,
            power=d["pw"],
            variance=d["var"],
            range_limit=d["rl"],
            cast_time=d["ct"],
            duration=d["dur"],
            ticks=d["tk"],
            flags=Behavior(d["fl"]),
            targeting=Targeting(d["tg"]),
            spawned_obj=spawned,
            audio_name=d["aud"],
            spell_type=d["typ"],
            animation_name=d["anm"],
            animation_scale=d["asc"],
            animate_on_target=d["aot"]
        )
    def serialize(self) -> str:
        return json.dumps({
            "sid": self.spell_id,
            "eid": self.effect_id,
            "seq": list(self.spell_sequence) if self.spell_sequence else None,
            "pw": self.power,
            "var": self.variance,
            "rl": self.range_limit,
            "ct": self.cast_time,
            "dur": self.duration,
            "tk": self.ticks,
            "fl": self.flags.value,
            "tg": self.targeting.value,
            "spn": (
                json.loads(self.spawned_obj.serialize())
                if self.spawned_obj is not None else None
            ),
            "aud": self.audio_name,
            "typ": self.spell_type,
            "anm": self.animation_name,
            "asc": self.animation_scale,
            "aot": self.animate_on_target
        })


    @property
    def copy_obj_controls(self) -> Iterable[Controls]:
        if self.spawned_obj is not None:
            if self.spawned_obj.obj_controls is not None:
                for controls in self.spawned_obj.obj_controls:
                    yield controls.create_copy()

    @property
    def should_play_audio(self) -> bool:
        return bool(self.audio_name)

    @property
    def should_play_animation(self) -> bool:
        return bool(self.animation_name)

    @property
    def has_range_limit(self) -> bool:
        return self.range_limit > 0.0

    @property
    def has_aura_apply(self) -> bool:
        return Behavior.AURA_APPLY in self.flags
    @property
    def has_aura_cancel(self) -> bool:
        return Behavior.AURA_CANCEL in self.flags

    @property
    def is_target_of_target(self) -> bool:
        return Behavior.TARGET_OF_TARGET in self.flags

    @property
    def is_area_of_effect(self) -> bool:
        return Behavior.AOE in self.flags

    @property
    def has_cascading_events(self) -> bool:
        return (
            self.is_area_of_effect or
            self.has_aura_apply or
            self.spawned_obj is not None or
            self.spell_sequence is not None
        )