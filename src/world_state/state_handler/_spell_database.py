from typing import Iterable
from ._spell_data_configs import LegacySpellConfig
from ._spell_data import SpellData, TargetingSpellFlags

from ._casting_system import CastingSystem, SpellCastingData, CastingBehavior
from ._health_system import HealthSystem, SpellHealthData, HealthBehavior
from ._movement_system import MovementSystem, SpellMovementData, MovementBehavior
from ._targeting_system import TargetingSystem, SpellTargetingData, TargetingBehavior, Targeting
from ._vfx_and_sfx_system import VfxAndSfxSystem, SpellVfxData, SpellVisualTemplate


class SpellDatabase:
    def __init__(self) -> None:
        self.spells_loaded_into_memory: dict[int, SpellData] = self._load_spells_into_memory()

    def get_spell(self, spell_id: int) -> SpellData:
        assert spell_id in self.spells_loaded_into_memory, f"Spell with ID {spell_id} not found."
        return self.spells_loaded_into_memory[spell_id]

    def get_all_spells(self) -> Iterable[SpellData]:
        """Yields all configured NewSpell instances."""
        return self.spells_loaded_into_memory.values()

    # --- System Factories ---

    def create_casting_system(self) -> CastingSystem:
        spell_data_dct = {
            spell_id: SpellCastingData(
                flags=CastingBehavior(spell.casting_behavior.value),
                timeline=spell.timeline,
                base_cooldown=spell.base_cooldown,
                hardware_bindings=spell.hardware_bindings,
                gcd_mod=spell.gcd_mod,
            )
            for spell_id, spell in self.spells_loaded_into_memory.items()
        }
        return CastingSystem(spell_data_dct)


    def create_health_system(self) -> HealthSystem:
        spell_data_dct = {
            spell_id: SpellHealthData(
                power=spell.power,
                flags=HealthBehavior(spell.health_behavior.value),
                hp=spell.hp,
            )
            for spell_id, spell in self.spells_loaded_into_memory.items()
        }
        return HealthSystem(spell_data_dct)


    def create_movement_system(self) -> MovementSystem:
        spell_data_dct = {
            spell_id: SpellMovementData(
                power=spell.power,
                range_limit=spell.range_limit,
                flags=MovementBehavior(spell.movement_behavior.value),
                spawned_x_offset=spell.spawned_x_offset,
                spawned_y_offset=spell.spawned_y_offset,
                spawned_movespeed=spell.spawned_movespeed,
            )
            for spell_id, spell in self.spells_loaded_into_memory.items()
        }
        return MovementSystem(spell_data_dct)


    def create_targeting_system(self) -> TargetingSystem:
        spell_data_dct = {}
        for spell_id, spell in self.spells_loaded_into_memory.items():
            is_enemy = bool(
                spell.targeting_behavior & TargetingSpellFlags.SPAWN_BOSS
            )
            is_boss_or_player = bool(
                spell.targeting_behavior
                & (TargetingSpellFlags.SPAWN_BOSS | TargetingSpellFlags.SPAWN_PLAYER)
            )

            spell_data_dct[spell_id] = SpellTargetingData(
                spell_id=spell.spell_id,
                targeting=Targeting(spell.targeting.value),
                is_enemy=is_enemy,
                is_boss_or_player=is_boss_or_player,
                flags=TargetingBehavior(spell.targeting_behavior.value),
            )
        return TargetingSystem(spell_data_dct)


    def create_vfx_and_sfx_system(self) -> VfxAndSfxSystem:
        spell_data_dct = {}
        for spell_id, spell in self.spells_loaded_into_memory.items():
            spawn_template = None
            if spell.spawn_color is not None:
                spawn_template = SpellVisualTemplate(
                    color=spell.spawn_color,
                    sprite_name=spell.spawn_sprite_name,
                    audio_name=spell.spawn_audio_name,
                )
            spell_data_dct[spell_id] = SpellVfxData(
                audio_name=spell.audio_name,
                animation_name=spell.animation_name,
                animation_scale=spell.animation_scale,
                animate_on_target=spell.animate_on_target,
                spawn_template=spawn_template,
            )
        return VfxAndSfxSystem(spell_data_dct)

    # --- Internal Config Loader ---

    @staticmethod
    def _load_spells_into_memory() -> dict[int, SpellData]:
        spells_loaded_into_memory: dict[int, SpellData] = {}

        # Load exactly what is explicitly written in the config file
        for spell in LegacySpellConfig.get_all_spells():
            assert spell.spell_id not in spells_loaded_into_memory, f"Spell with ID {spell.spell_id} already exists."
            spells_loaded_into_memory[spell.spell_id] = spell

        return spells_loaded_into_memory