from src.config import AudioFiles, Colors, Consts
from src.models import Controls, GameObj, SpellFlag, SpellTarget, Spell
from src.handlers.spell_factory import SpellFactory, SpellTemplates
from src.templates.basic_movement import BasicMovement
from src.templates.basic_targeting import BasicTargeting
from src.templates.basic_spawning import BasicSpawning


class NpcLandmine:
    @staticmethod
    def landmine_explosion_tick() -> SpellFactory:
        return (
            SpellTemplates.damage_enemies_within_range(114, 150.0, 0.1)
            .despawn_self()
        )

    @staticmethod
    def landmine_explosion_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(115, NpcLandmine.landmine_explosion_tick().spell_id, 15.0, 150)

    @staticmethod
    def spawn_landmine() -> SpellFactory:
        game_obj = GameObj(
            hp=20.0,
            x=0.2,
            y=0.8,
            color=Colors.MAGENTA,
            ability_1_id=NpcLandmine.landmine_explosion_apply().spell_id,
        )
        obj_controls = (
            Controls(timeline_timestamp=1.5, ability_1=True),
        )
        return (
            SpellFactory(71)
            .spawn_obj(game_obj)
            .add_controls(obj_controls)
        )
