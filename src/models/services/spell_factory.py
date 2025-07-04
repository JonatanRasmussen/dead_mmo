from typing import Optional, Tuple
from src.config import Consts
from src.models.components import Behavior, Controls, GameObj, Hostility, Targeting, Spell


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
        self.spell.flags |= new_flag
        return self

    def _remove_flag(self, removed_flag: Behavior) -> 'SpellFactory':
        assert (self.spell.flags & removed_flag), f"Flag {removed_flag} is not currently set in {self.spell.flags}"
        self.spell.flags &= ~removed_flag
        return self

    def set_audio(self, audio_file_name: str) -> 'SpellFactory':
        assert (self.spell.audio_name == ""), f"Spell audio is already set to {self.spell.audio_name}."
        self.spell.audio_name = audio_file_name
        return self

    def use_gcd(self) -> 'SpellFactory':
        return self.add_flag(Behavior.TRIGGER_GCD)

    def aoe_cast(self) -> 'SpellFactory':
        return self.add_flag(Behavior.AOE)

    def despawn_self(self) -> 'SpellFactory':
        return self.add_flag(Behavior.DESPAWN_SELF)

    def teleport_to_parent(self) -> 'SpellFactory':
        return self.add_flag(Behavior.TELEPORT_TO_TARGET).set_targeting(Targeting.PARENT)

    def set_spell_sequence(self, sequence: tuple[int, ...]) -> 'SpellFactory':
        self.spell.spell_sequence = sequence
        return self

    def apply_aura(self, periodic_spell_id: int, duration: int, ticks: int) -> 'SpellFactory':
        self.spell.duration = duration
        self.spell.ticks = ticks
        self.spell.effect_id = periodic_spell_id
        return self.add_flag(Behavior.AURA_APPLY)

    def cancel_aura(self, periodic_spell_id: int) -> 'SpellFactory':
        self.spell.effect_id = periodic_spell_id
        return self.add_flag(Behavior.AURA_CANCEL)

    def inflict_damage(self, spell_power: float) -> 'SpellFactory':
        assert not (self.spell.flags & Behavior.HEALING), f"{self.spell.spell_id} with HEALING flag cannot be set to apply damage."
        assert not (self.spell.flags & Behavior.DAMAGING), f"{self.spell.spell_id} is already set to apply damage."
        self.spell.power = spell_power
        return self.add_flag(Behavior.DAMAGING)

    def restore_health(self, spell_power: float) -> 'SpellFactory':
        assert not (self.spell.flags & Behavior.DAMAGING), f"{self.spell.spell_id} with DAMAGING flag cannot be set to apply healing."
        assert not (self.spell.flags & Behavior.HEALING), f"{self.spell.spell_id} is already set to apply healing."
        self.spell.power = spell_power
        return self.add_flag(Behavior.HEALING)

    def set_range_limit(self, radius: float) -> 'SpellFactory':
        assert (self.spell.range_limit == Spell().range_limit), f"Range limit is already set to {self.spell.range_limit}."
        self.spell.range_limit = radius
        return self

    def cast_on_self(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.SELF)

    def cast_on_target(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.TARGET)

    def cast_on_parent(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.PARENT)

    def cast_on_default_friendly(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.DEFAULT_FRIENDLY)

    def cast_on_default_enemy(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.DEFAULT_ENEMY)

    def cast_on_next_tab_target(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.TAB_TO_NEXT)

    def update_current_target(self) -> 'SpellFactory':
        return self.add_flag(Behavior.UPDATE_CURRENT_TARGET)

    def cast_on_target_of_target(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.TARGET).add_flag(Behavior.TARGET_OF_TARGET)

    def add_controls(self, controls: tuple[Controls, ...]) -> 'SpellFactory':
        self.spell.obj_controls = controls
        return self

    def spawn_minion(self, game_obj: GameObj, controls: tuple[Controls, ...]) -> 'SpellFactory':
        return self._spawn_obj(game_obj).add_controls(controls).cast_on_self()

    def spawn_projectile(self, game_obj: GameObj, controls: tuple[Controls, ...]) -> 'SpellFactory':
        return self._spawn_obj(game_obj).add_controls(controls).cast_on_target()

    def spawn_player(self, game_obj: GameObj) -> 'SpellFactory':
        game_obj.team = Hostility.ALLIED
        return self._spawn_obj(game_obj).add_flag(Behavior.SPAWN_PLAYER).cast_on_self()

    def spawn_boss(self, game_obj: GameObj, controls: tuple[Controls, ...]) -> 'SpellFactory':
        game_obj.team = Hostility.ENEMY
        return self.add_flag(Behavior.SPAWN_BOSS).spawn_minion(game_obj, controls)

    def _spawn_obj(self, game_obj: GameObj) -> 'SpellFactory':
        game_obj.spawned_from_spell=self.spell.spell_id
        self.spell.spawned_obj = game_obj
        return self.add_flag(Behavior.SPAWN_OBJ)

    def set_targeting(self, targeting: Targeting) -> 'SpellFactory':
        assert (self.spell.targeting == Targeting.NONE), f"Targeting is already set to {self.spell.targeting}."
        self.spell.targeting = targeting
        return self


class SpellTemplates:

    @staticmethod
    def step_move_self(spell_id: int, direction: Behavior) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .add_flag(direction)
        )

    @staticmethod
    def apply_aura_to_self(spell_id: int, periodic_spell_id: int, duration: int, ticks: int) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .apply_aura(periodic_spell_id, duration, ticks)
        )

    @staticmethod
    def start_move_self(spell_id: int, periodic_spell_id: int) -> SpellFactory:
        updates_per_second = Consts.MOVEMENT_UPDATES_PER_SECOND
        return SpellTemplates.apply_aura_to_self(spell_id, periodic_spell_id, 60000, 60*updates_per_second)

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
            .cast_on_target()
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
            .cast_on_target()
            .inflict_damage(power)
            .set_range_limit(radius)
        )

    @staticmethod
    def heal_current_target(spell_id: int, power: float) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_target()
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
            .cast_on_target()
            .restore_health(power)
            .set_range_limit(radius)
        )