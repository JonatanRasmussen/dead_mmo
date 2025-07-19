from src.settings import AudioFiles, Colors, Consts
from src.models.components import Controls, Distance, GameObj, Faction, KeyPresses, Loadout, Position, Resources
from src.models.data import Behavior, Targeting, Spell
from src.configs.blueprints import SpellFactory, SpellTemplates, GameObjFactory, GameObjTemplates
from .basic_movement import BasicMovement
from .basic_targeting import BasicTargeting


class NpcLandmine:
    @staticmethod
    def landmine_explosion_tick() -> SpellFactory:
        return (
            SpellTemplates.damage_enemies_within_range(114, 150.0, 0.1)
            .despawn_self()
        )

    @staticmethod
    def landmine_explosion_apply() -> SpellFactory:
        return SpellTemplates.apply_aura_to_self(115, NpcLandmine.landmine_explosion_tick().spell_id, 15000, 150)

    @staticmethod
    def spawn_landmine() -> SpellFactory:
        timeline = {1500: NpcLandmine.landmine_explosion_apply().spell_id}
        obj_template = GameObjTemplates.create_enemy(timeline, x=-0.5, y=0.1, hp=20.0, color=Colors.MAGENTA)
        return (
            SpellFactory(71)
            .spawn_minion(obj_template)
        )
