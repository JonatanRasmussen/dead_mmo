from typing import Optional, Tuple
from src.config import Consts
from src.models.components import GameObj, Controls, Behavior, Targeting, Spell


class SpellFactory:
    def __init__(self, spell_id: int) -> None:
        self.spell: Spell = Spell(spell_id=spell_id)

    @property
    def spell_id(self) -> int:
        return self.spell.spell_id

    def build(self) -> Spell:
        return self.spell

    def add_flag(self, new_flag: Behavior) -> 'SpellFactory':
        assert not (self.spell.flags & new_flag), f"Flag {new_flag} is already set in {self.spell.flags}"
        self.spell = self.spell._replace(flags=self.spell.flags | new_flag)
        return self

    def remove_flag(self, removed_flag: Behavior) -> 'SpellFactory':
        assert (self.spell.flags & removed_flag), f"Flag {removed_flag} is not currently set in {self.spell.flags}"
        self.spell = self.spell._replace(flags=self.spell.flags & ~removed_flag)
        return self

    def set_audio(self, audio_file_name: str) -> 'SpellFactory':
        assert (self.spell.audio_name is not None), f"Spell audio is already set to {self.spell.audio_name}."
        self.spell = self.spell._replace(audio_name=audio_file_name)
        return self

    def cast_on_self(self) -> 'SpellFactory':
        return self._set_targeting(Targeting.SELF)

    def cast_on_parent(self) -> 'SpellFactory':
        return self._set_targeting(Targeting.PARENT)

    def cast_on_aura_target(self) -> 'SpellFactory':
        return self._set_targeting(Targeting.AURA_TARGET)

    def cast_on_current_target(self) -> 'SpellFactory':
        return self._set_targeting(Targeting.CURRENT_TARGET)

    def cast_on_default_friendly(self) -> 'SpellFactory':
        return self._set_targeting(Targeting.DEFAULT_FRIENDLY)

    def cast_on_default_enemy(self) -> 'SpellFactory':
        return self._set_targeting(Targeting.DEFAULT_ENEMY)

    def cast_on_next_tab_target(self) -> 'SpellFactory':
        return self._set_targeting(Targeting.TAB_TO_NEXT)

    def update_current_target(self) -> 'SpellFactory':
        return self.add_flag(Behavior.UPDATE_CURRENT_TARGET)

    def cast_on_target_of_target(self) -> 'SpellFactory':
        return self.add_flag(Behavior.TARGET_OF_TARGET)

    def use_gcd(self) -> 'SpellFactory':
        return self.add_flag(Behavior.TRIGGER_GCD)

    def despawn_self(self) -> 'SpellFactory':
        return self.add_flag(Behavior.DESPAWN_SELF)

    def teleport_to_parent(self) -> 'SpellFactory':
        return self.add_flag(Behavior.TELEPORT_TO_TARGET).cast_on_parent()

    def set_spell_sequence(self, sequence: Tuple[int, ...]) -> 'SpellFactory':
        self.spell = self.spell._replace(spell_sequence=sequence)
        return self

    def apply_aura(self, periodic_spell_id: int, duration: float, ticks: int) -> 'SpellFactory':
        self.spell = self.spell._replace(duration=duration, ticks=ticks, external_spell=periodic_spell_id)
        return self.add_flag(Behavior.AURA_APPLY)

    def cancel_aura(self, periodic_spell_id: int) -> 'SpellFactory':
        self.spell = self.spell._replace(external_spell=periodic_spell_id)
        return self.add_flag(Behavior.AURA_CANCEL)

    def add_controls(self, controls: Tuple[Controls, ...]) -> 'SpellFactory':
        self.spell = self.spell._replace(obj_controls=controls)
        return self

    def spawn_minion(self, game_obj: GameObj) -> 'SpellFactory':
        return self._spawn_obj(game_obj).cast_on_self()

    def spawn_projectile(self, game_obj: GameObj) -> 'SpellFactory':
        return self._spawn_obj(game_obj).cast_on_current_target()

    def spawn_boss(self, game_obj: GameObj) -> 'SpellFactory':
        obj_to_spawn = game_obj._replace(is_allied=False)
        return self.add_flag(Behavior.SPAWN_BOSS).spawn_minion(obj_to_spawn)

    def spawn_player(self, game_obj: GameObj) -> 'SpellFactory':
        obj_to_spawn = game_obj._replace(is_allied=True)
        return self.add_flag(Behavior.SPAWN_PLAYER).spawn_minion(obj_to_spawn)

    def inflict_damage(self, spell_power: float) -> 'SpellFactory':
        assert not (self.spell.flags & Behavior.HEALING), f"{self.spell.spell_id} with HEALING flag cannot be set to apply damage."
        assert not (self.spell.flags & Behavior.DAMAGING), f"{self.spell.spell_id} is already set to apply damage."
        self.spell = self.spell._replace(power=spell_power)
        return self.add_flag(Behavior.DAMAGING)

    def restore_health(self, spell_power: float) -> 'SpellFactory':
        assert not (self.spell.flags & Behavior.DAMAGING), f"{self.spell.spell_id} with DAMAGING flag cannot be set to apply healing."
        assert not (self.spell.flags & Behavior.HEALING), f"{self.spell.spell_id} is already set to apply healing."
        self.spell = self.spell._replace(power=spell_power)
        return self.add_flag(Behavior.HEALING)

    def set_range_limit(self, radius: float) -> 'SpellFactory':
        assert (self.spell.range_limit == Spell().range_limit), f"Range limit is already set to {self.spell.range_limit}."
        self.spell = self.spell._replace(range_limit=radius)
        return self

    def _spawn_obj(self, game_obj: GameObj) -> 'SpellFactory':
        obj_to_spawn = game_obj._replace(spawned_from_spell=self.spell.spell_id)
        self.spell = self.spell._replace(spawned_obj=obj_to_spawn)
        return self.add_flag(Behavior.SPAWN_OBJ)

    def _set_targeting(self, targeting: Targeting) -> 'SpellFactory':
        assert (self.spell.targeting == Targeting.NONE), f"Targeting is already set to {targeting}."
        self.spell = self.spell._replace(targeting=targeting)
        return self


class SpellTemplates:

    @staticmethod
    def step_move_self(spell_id: int, direction: Behavior) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .add_flag(direction)
            .add_flag(Behavior.DENY_IF_CASTING)
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
        updates_per_second = Consts.MOVEMENT_UPDATES_PER_SECOND
        return SpellTemplates.apply_aura_to_self(spell_id, periodic_spell_id, 60.0, 60*updates_per_second)

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