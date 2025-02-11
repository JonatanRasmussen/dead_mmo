from typing import List
from src.config.color import Color
from src.model.models import SpellFlag, Spell, Controls, GameObj
from src.utils.utils import Utils


class Database:
    def __init__(self) -> None:
        self.spells: List[Spell] = Database.load_spell_collections()

    @staticmethod
    def load_spell_collections() -> List[Spell]:
        spells: List[Spell] = []
        spells += Utils.load_collection(SpellCollectionCore)
        return spells


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
            flags=SpellFlag.HEAL | SpellFlag.SELF_CAST,
        )

    @staticmethod
    def healing_aura() -> Spell:
        return Spell(
            spell_id=102,
            aura_effect_id=SpellCollectionCore.small_heal().spell_id,
            duration=6.0,
            ticks=10,
            power=20.0,
            flags=SpellFlag.AURA | SpellFlag.SELF_CAST | SpellFlag.HEAL,
        )

    @staticmethod
    def spawn_player() -> Spell:
        spell_id = 200
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_PLAYER | SpellFlag.SELF_CAST,
            spawned_obj=GameObj(
                spawned_from_spell=spell_id,
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
            ),
        )

    @staticmethod
    def spawn_enemy() -> Spell:
        spell_id = 201
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SELF_CAST,
            spawned_obj=GameObj(
                spawned_from_spell=spell_id,
                hp=30.0,
                color=Color.GREEN,
                x=0.7,
                y=0.7,
                ability_1_id=SpellCollectionCore.small_heal().spell_id,
                ability_2_id=SpellCollectionCore.healing_aura().spell_id,
            ),
            controls=(
                Controls(local_timestamp=3.0, ability_1=True),
                Controls(local_timestamp=5.0, ability_2=True),
            )
        )

    @staticmethod
    def spawn_target_dummy() -> Spell:
        spell_id = 202
        return Spell(
            spell_id=spell_id,
            flags=SpellFlag.SPAWN_BOSS | SpellFlag.SELF_CAST,
            spawned_obj=GameObj(
                spawned_from_spell=spell_id,
                hp=80.0,
                color=Color.BLUE,
                x=0.5,
                y=0.8,
                ability_1_id=SpellCollectionCore.fireblast().spell_id,
            ),
            controls=(
                Controls(local_timestamp=4.0, ability_1=True),
            )
        )

    @staticmethod
    def setup_test_zone() -> Spell:
        return Spell(
            spell_id=300,
            spell_sequence=(
                SpellCollectionCore.spawn_enemy().spell_id,
                SpellCollectionCore.spawn_target_dummy().spell_id,
                SpellCollectionCore.spawn_player().spell_id,
            ),
        )