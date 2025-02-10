from typing import List
from src.config.color import Color
from src.model.models import SpellFlag, Spell, PlayerInput, GameObj
from src.utils.utils import Utils


class Database:
    def __init__(self) -> None:
        self.spells: List[Spell] = Database.load_spell_collections()
        self.obj_templates: List[GameObj] = Database.load_obj_template_collections()

    @staticmethod
    def load_spell_collections() -> List[Spell]:
        spells: List[Spell] = []
        spells += Utils.load_collection(SpellCollectionCore)
        return spells

    @staticmethod
    def load_obj_template_collections() -> List[GameObj]:
        obj_templates: List[GameObj] = []
        obj_templates += Utils.load_collection(ObjTemplateCollectionCore)
        return obj_templates


class SpellCollectionCore:
    @staticmethod
    def empty_spell() -> Spell:
        return Spell(spell_id=0)

    @staticmethod
    def move_up() -> Spell:
        return Spell(spell_id=1, flags=SpellFlag.MOVE_UP | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST)
    @staticmethod
    def move_left() -> Spell:
        return Spell(spell_id=2, flags=SpellFlag.MOVE_LEFT | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST)
    @staticmethod
    def move_down() -> Spell:
        return Spell(spell_id=3, flags=SpellFlag.MOVE_DOWN | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST)
    @staticmethod
    def move_right() -> Spell:
        return Spell(spell_id=4, flags=SpellFlag.MOVE_RIGHT | SpellFlag.DENY_IF_CASTING | SpellFlag.SELF_CAST)
    @staticmethod
    def tab_target() -> Spell:
        return Spell(spell_id=5, flags=SpellFlag.TAB_TARGET)

    @staticmethod
    def fireblast() -> Spell:
        return Spell(
            spell_id=100,
            power=3.0,
            flags=SpellFlag.DAMAGE | SpellFlag.TRIGGER_GCD,
        )

    @staticmethod
    def small_heal() -> Spell:
        return Spell(
            spell_id=101,
            duration=6.0,
            ticks=10,
            power=20.0,
            flags=SpellFlag.HEAL,
        )

    @staticmethod
    def healing_aura() -> Spell:
        return Spell(
            spell_id=102,
            next_spell=SpellCollectionCore.small_heal().spell_id,
            flags=SpellFlag.AURA | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def spawn_player() -> Spell:
        return Spell(
            spell_id=200,
            flags=SpellFlag.SPAWN_PLAYER | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def spawn_enemy() -> Spell:
        return Spell(
            spell_id=201,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def spawn_target_dummy() -> Spell:
        return Spell(
            spell_id=202,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def setup_test_zone() -> Spell:
        return Spell(
            spell_id=300,
            next_spell=SpellCollectionCore.setup_test_zone_seq1().spell_id,
        )

    @staticmethod
    def setup_test_zone_seq1() -> Spell:
        return SpellCollectionCore.spawn_enemy()._replace(
            spell_id=301,
            alias_id=SpellCollectionCore.spawn_enemy().spell_id,
            next_spell=SpellCollectionCore.setup_test_zone_seq2().spell_id,
        )

    @staticmethod
    def setup_test_zone_seq2() -> Spell:
        return SpellCollectionCore.spawn_target_dummy()._replace(
            spell_id=302,
            alias_id=SpellCollectionCore.spawn_target_dummy().spell_id,
            next_spell=SpellCollectionCore.spawn_player().spell_id,
        )


class ObjTemplateCollectionCore:
    @staticmethod
    def empty_obj() -> GameObj:
        return GameObj(
            template_id=0,
        )


    @staticmethod
    def player_template() -> GameObj:
        return GameObj(
            template_id=SpellCollectionCore.spawn_player().spell_id,
            hp=30.0,
            is_allied=True,
            color=Color.RED,
            x=0.3,
            y=0.3,
            move_up_id=SpellCollectionCore.move_up().spell_id,
            move_left_id=SpellCollectionCore.move_left().spell_id,
            move_down_id=SpellCollectionCore.move_down().spell_id,
            move_right_id=SpellCollectionCore.move_right().spell_id,
            next_target=SpellCollectionCore.tab_target().spell_id,
            ability_1_id=SpellCollectionCore.fireblast().spell_id,
            ability_2_id=SpellCollectionCore.fireblast().spell_id,
            ability_3_id=SpellCollectionCore.fireblast().spell_id,
            ability_4_id=SpellCollectionCore.fireblast().spell_id,
        )

    @staticmethod
    def enemy_template() -> GameObj:
        return GameObj(
            template_id=SpellCollectionCore.spawn_enemy().spell_id,
            hp=30.0,
            color=Color.GREEN,
            x=0.7,
            y=0.7,
            ability_1_id=SpellCollectionCore.small_heal().spell_id,
            ability_2_id=SpellCollectionCore.healing_aura().spell_id,
            inputs=Utils.create_player_input_dct([
                PlayerInput(local_timestamp=3.0, ability_1=True),
                PlayerInput(local_timestamp=5.0, ability_2=True),
            ]),
        )

    @staticmethod
    def target_dummy_template() -> GameObj:
        return GameObj(
            template_id=SpellCollectionCore.spawn_target_dummy().spell_id,
            hp=80.0,
            color=Color.BLUE,
            x=0.5,
            y=0.8,
            ability_1_id=SpellCollectionCore.fireblast().spell_id,
            inputs=Utils.create_player_input_dct([
                PlayerInput(local_timestamp=4.0, ability_1=True),
            ]),
        )