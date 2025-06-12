from typing import Optional, Tuple

from src.models.game_obj import GameObj, Controls
from src.models.spell import SpellFlag, SpellTarget, Spell


class SpellFactory:
    def __init__(self, spell_id: int) -> None:
        self.spell: Spell = Spell(spell_id=spell_id)

    @property
    def spell_id(self) -> int:
        return self.spell.spell_id

    def build(self) -> Spell:
        return self.spell

    def add_flag(self, new_flag: SpellFlag) -> 'SpellFactory':
        assert not (self.spell.flags & new_flag), f"Flag {new_flag} is already set in {self.spell.flags}"
        self.spell = self.spell._replace(flags=self.spell.flags | new_flag)
        return self

    def remove_flag(self, removed_flag: SpellFlag) -> 'SpellFactory':
        assert (self.spell.flags & removed_flag), f"Flag {removed_flag} is not currently set in {self.spell.flags}"
        self.spell = self.spell._replace(flags=self.spell.flags & ~removed_flag)
        return self

    def set_audio(self, audio_file_name: str) -> 'SpellFactory':
        assert (self.spell.audio_name is not None), f"Spell audio is already set to {self.spell.audio_name}."
        self.spell = self.spell._replace(audio_name=audio_file_name)
        return self

    def set_targeting(self, targeting: SpellTarget) -> 'SpellFactory':
        assert (self.spell.targeting == SpellTarget.NONE), f"Targeting is already set to {targeting}."
        self.spell = self.spell._replace(targeting=targeting)
        return self

    def cast_on_self(self) -> 'SpellFactory':
        return self.set_targeting(SpellTarget.SELF)

    def cast_on_parent(self) -> 'SpellFactory':
        return self.set_targeting(SpellTarget.PARENT)

    def cast_on_aura_target(self) -> 'SpellFactory':
        return self.set_targeting(SpellTarget.AURA_TARGET)

    def cast_on_current_target(self) -> 'SpellFactory':
        return self.set_targeting(SpellTarget.CURRENT_TARGET)

    def cast_on_default_friendly(self) -> 'SpellFactory':
        return self.set_targeting(SpellTarget.DEFAULT_FRIENDLY)

    def cast_on_default_enemy(self) -> 'SpellFactory':
        return self.set_targeting(SpellTarget.DEFAULT_ENEMY)

    def cast_on_next_tab_target(self) -> 'SpellFactory':
        return self.set_targeting(SpellTarget.TAB_TO_NEXT)

    def update_current_target(self) -> 'SpellFactory':
        return self.add_flag(SpellFlag.UPDATE_CURRENT_TARGET)

    def cast_on_target_of_target(self) -> 'SpellFactory':
        return self.add_flag(SpellFlag.TARGET_OF_TARGET)

    def use_gcd(self) -> 'SpellFactory':
        return self.add_flag(SpellFlag.TRIGGER_GCD)

    def despawn_self(self) -> 'SpellFactory':
        return self.add_flag(SpellFlag.DESPAWN_SELF)

    def teleport_to_parent(self) -> 'SpellFactory':
        return self.add_flag(SpellFlag.TELEPORT_TO_TARGET).cast_on_parent()

    def set_spell_sequence(self, sequence: Tuple[int, ...]) -> 'SpellFactory':
        self.spell = self.spell._replace(spell_sequence=sequence)
        return self

    def apply_aura(self, periodic_spell_id: int, duration: float, ticks: int) -> 'SpellFactory':
        self.spell = self.spell._replace(duration=duration, ticks=ticks, external_spell=periodic_spell_id)
        return self.add_flag(SpellFlag.AURA_APPLY)

    def cancel_aura(self, periodic_spell_id: int) -> 'SpellFactory':
        self.spell = self.spell._replace(external_spell=periodic_spell_id)
        return self.add_flag(SpellFlag.AURA_CANCEL)

    def add_controls(self, controls: Tuple[Controls, ...]) -> 'SpellFactory':
        self.spell = self.spell._replace(obj_controls=controls)
        return self

    def spawn_obj(self, game_obj: GameObj) -> 'SpellFactory':
        obj_to_spawn = game_obj._replace(spawned_from_spell=self.spell.spell_id)
        self.spell = self.spell._replace(spawned_obj=obj_to_spawn)
        return self.cast_on_self().add_flag(SpellFlag.SPAWN_OBJ)

    def spawn_boss(self, game_obj: GameObj) -> 'SpellFactory':
        obj_to_spawn = game_obj._replace(is_allied=False)
        return self.add_flag(SpellFlag.SPAWN_BOSS).spawn_obj(obj_to_spawn)

    def spawn_player(self, game_obj: GameObj) -> 'SpellFactory':
        obj_to_spawn = game_obj._replace(is_allied=True)
        return self.add_flag(SpellFlag.SPAWN_PLAYER).spawn_obj(obj_to_spawn)

    def inflict_damage(self, spell_power: float) -> 'SpellFactory':
        assert not (self.spell.flags & SpellFlag.HEALING), f"{self.spell.spell_id} with HEALING flag cannot be set to apply damage."
        assert not (self.spell.flags & SpellFlag.DAMAGING), f"{self.spell.spell_id} is already set to apply damage."
        self.spell = self.spell._replace(power=spell_power)
        return self.add_flag(SpellFlag.DAMAGING)

    def restore_health(self, spell_power: float) -> 'SpellFactory':
        assert not (self.spell.flags & SpellFlag.DAMAGING), f"{self.spell.spell_id} with DAMAGING flag cannot be set to apply healing."
        assert not (self.spell.flags & SpellFlag.HEALING), f"{self.spell.spell_id} is already set to apply healing."
        self.spell = self.spell._replace(power=spell_power)
        return self.add_flag(SpellFlag.HEALING)

    def set_range_limit(self, radius: float) -> 'SpellFactory':
        assert (self.spell.range_limit == Spell().range_limit), f"Range limit is already set to {self.spell.range_limit}."
        self.spell = self.spell._replace(range_limit=radius)
        return self


class SpellTemplates:

    @staticmethod
    def step_move_self(spell_id: int, direction: SpellFlag) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .add_flag(direction)
            .add_flag(SpellFlag.DENY_IF_CASTING)
        )

    @staticmethod
    def apply_aura_to_self(spell_id: int, periodic_spell_id: int, duration: float, ticks: int) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .apply_aura(periodic_spell_id, duration, ticks)
        )

    @staticmethod
    def start_move_self(spell_id: int, periodic_spell_id: int) -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(spell_id, periodic_spell_id, 60.0, 60*250)

    @staticmethod
    def cancel_aura_on_self(spell_id: int, aura_spell_id: int) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .cancel_aura(aura_spell_id)
        )

    @staticmethod
    def damage_current_target(spell_id: int, power: float) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_current_target()
            .inflict_damage(power)
        )

    @staticmethod
    def damage_enemies_within_range(spell_id: int, power: float, radius: float) -> 'SpellFactory':
        return (
            SpellFactory(spell_id)
            .cast_on_default_enemy()
            .inflict_damage(power)
            .set_range_limit(radius)
        )

    @staticmethod
    def damage_current_target_when_within_range(spell_id: int, power: float, radius: float) -> 'SpellFactory':
        return (
            SpellFactory(spell_id)
            .cast_on_current_target()
            .inflict_damage(power)
            .set_range_limit(radius)
        )

    @staticmethod
    def heal_current_target(spell_id: int, power: float) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_current_target()
            .restore_health(power)
        )

    @staticmethod
    def heal_allies_within_range(spell_id: int, power: float, radius: float) -> 'SpellFactory':
        return (
            SpellFactory(spell_id)
            .cast_on_default_friendly()
            .restore_health(power)
            .set_range_limit(radius)
        )

    @staticmethod
    def heal_current_target_when_within_range(spell_id: int, power: float, radius: float) -> 'SpellFactory':
        return (
            SpellFactory(spell_id)
            .cast_on_current_target()
            .restore_health(power)
            .set_range_limit(radius)
        )