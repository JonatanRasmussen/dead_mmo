from src.settings import Consts
from dataclasses import dataclass, field


@dataclass(slots=True)
class SpellDef:
    spell_id: int = Consts.EMPTY_SPELL_ID
    name: str = ""
    validations: dict[str, float] = field(default_factory=dict)
    effects: dict[str, float] = field(default_factory=dict)
    cascade: list[int] = field(default_factory=list)
    timeline: dict[int, list[int]] = field(default_factory=dict)
    aoe_spell_id: int = Consts.EMPTY_SPELL_ID
    signal_spell_id: int = Consts.EMPTY_SPELL_ID
