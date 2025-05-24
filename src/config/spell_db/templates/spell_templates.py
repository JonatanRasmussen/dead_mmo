from typing import Any, List, Dict, Type, Optional, Tuple
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, SpellTarget, Spell
from src.handlers.id_gen import IdGen


class SpellTemplates:

    # Uncategorized templates

    @staticmethod
    def empty_spell_template(spell_id: int) -> Spell:
        return Spell(
            spell_id=spell_id,
        )

    @staticmethod
    def apply_flag_to_self(spell_id: int, spell_flag: SpellFlag) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=spell_flag,
            targeting=SpellTarget.SELF_CAST,
        )


    @staticmethod
    def apply_targeting_to_self(spell_id: int, spell_targeting: SpellTarget) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SET_TARGET,
            targeting=spell_targeting,
        )

    # Movement templates

    @staticmethod
    def step_movement(spell_id: int, direction: SpellFlag) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=direction | SpellFlag.DENY_IF_CASTING,
            targeting=SpellTarget.SELF_CAST,
        )
    @staticmethod
    def begin_movement(spell_id: int, direction: SpellFlag) -> Spell:
        return Spell(
            spell_id=spell_id,
            duration=60.0,
            ticks=60*250,
            flags=SpellFlag.AURA_APPLY | direction,
            targeting=SpellTarget.SELF_CAST,
        )
    @staticmethod
    def cancel_movement(spell_id: int, referenced_spell: int) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.AURA_CANCEL,
            targeting=SpellTarget.SELF_CAST,
            referenced_spell=referenced_spell,
        )

    # Spawn templates

    @staticmethod
    def new_player(spell_id: int, spawned_obj: GameObj) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_PLAYER | SpellFlag.SPAWN_OBJ,
            targeting=SpellTarget.SELF_CAST,
            spawned_obj=spawned_obj._replace(
                spawned_from_spell=spell_id,
                is_allied=True,
            ),
        )

    @staticmethod
    def new_boss(spell_id: int, spawned_obj: GameObj, obj_controls: Optional[Tuple[Controls, ...]],) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SPAWN_OBJ,
            targeting=SpellTarget.SELF_CAST,
            spawned_obj=spawned_obj._replace(
                spawned_from_spell=spell_id,
            ),
            obj_controls=obj_controls
        )

    @staticmethod
    def new_hitbox(spell_id: int, spawned_obj: GameObj, obj_controls: Optional[Tuple[Controls, ...]],) -> Spell:
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_OBJ,
            targeting=SpellTarget.SELF_CAST,
            spawned_obj=spawned_obj._replace(
                spawned_from_spell=spell_id,
            ),
            obj_controls=obj_controls
        )

    # Combat templates

    @staticmethod
    def instant_damage(spell_id: int, power: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            flags=SpellFlag.DAMAGING | SpellFlag.TRIGGER_GCD,
            targeting=SpellTarget.CAST_ON_TARGET,
        )

    @staticmethod
    def instant_heal(spell_id: int, power: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            flags=SpellFlag.HEALING | SpellFlag.TRIGGER_GCD,
            targeting=SpellTarget.FRIENDLY_CAST,
        )

    @staticmethod
    def damaging_aura(spell_id: int, power: float, duration: float, ticks: int, range_limit: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            duration=duration,
            ticks=ticks,
            range_limit=range_limit,
            flags=SpellFlag.AURA_APPLY | SpellFlag.TRIGGER_GCD,
            targeting=SpellTarget.SELF_CAST,
        )

    @staticmethod
    def periodic_heal(spell_id: int, power: float, duration: float, ticks: int) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            duration=duration,
            ticks=ticks,
            flags=SpellFlag.AURA_APPLY | SpellFlag.HEALING | SpellFlag.TRIGGER_GCD,
            targeting=SpellTarget.FRIENDLY_CAST,
        )

    @staticmethod
    def hitbox_tick(spell_id: int, power: float, range_limit: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            range_limit=range_limit,
            flags=SpellFlag.HAS_RANGE_LIMIT | SpellFlag.DAMAGING,
            targeting=SpellTarget.HOSTILE_CAST,
        )

    @staticmethod
    def single_tick_hitbox(spell_id: int, power: float, range_limit: float) -> Spell:
        return Spell(
            spell_id=spell_id,
            power=power,
            range_limit=range_limit,
            flags=SpellFlag.HAS_RANGE_LIMIT | SpellFlag.DAMAGING | SpellFlag.DESPAWN_SELF,
            targeting=SpellTarget.HOSTILE_CAST,
        )

    # Instance setup templates

    @staticmethod
    def instance_setup(spell_id: int, spell_sequence: Optional[Tuple[int, ...]]) -> Spell:
        return Spell(
            spell_id=spell_id,
            spell_sequence=spell_sequence,
            targeting=SpellTarget.SELF_CAST,
        )

