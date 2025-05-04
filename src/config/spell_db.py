from typing import Any, List, Dict, Type
from src.config.color import Color

from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell


class SpellDatabase:
    def __init__(self) -> None:
        self.spells_loaded_into_memory: Dict[int, Spell] = SpellDatabase.load_spells_into_memory()

    @staticmethod
    def load_spells_into_memory() -> Dict[int, Spell]:
        spells_to_load: List[Spell] = []
        spells_to_load += SpellDatabase._load_collection(SpellCollectionCore)
        spells_loaded_into_memory: Dict[int, Spell] = {}
        for spell in spells_to_load:
            assert spell.spell_id not in spells_to_load, f"Spell with ID {spell.spell_id} already exists."
            spells_loaded_into_memory[spell.spell_id] = spell
        return spells_loaded_into_memory

    def get_spell(self, spell_id: int) -> Spell:
        assert spell_id in self.spells_loaded_into_memory, f"Spell with ID {spell_id} not found."
        return self.spells_loaded_into_memory.get(spell_id, Spell())

    @staticmethod
    def _load_collection(class_with_methods: Type[Any]) -> List[Any]:
        static_methods = [name for name, attr in class_with_methods.__dict__.items() if isinstance(attr, staticmethod)]
        return [getattr(class_with_methods, method)() for method in static_methods]


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
        return Spell(spell_id=5, flags=SpellFlag.TAB_TARGET | SpellFlag.SELF_CAST)

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
                start_move_up_id=SpellCollectionCore.move_up().spell_id,
                stop_move_up_id=SpellCollectionCore.move_up().spell_id,
                start_move_left_id=SpellCollectionCore.move_left().spell_id,
                stop_move_left_id=SpellCollectionCore.move_left().spell_id,
                start_move_down_id=SpellCollectionCore.move_down().spell_id,
                stop_move_down_id=SpellCollectionCore.move_down().spell_id,
                start_move_right_id=SpellCollectionCore.move_right().spell_id,
                stop_move_right_id=SpellCollectionCore.move_right().spell_id,
                next_target_id=SpellCollectionCore.tab_target().spell_id,
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
            obj_controls=(
                Controls(timestamp=3.0, ability_1=True),
                Controls(timestamp=5.0, ability_2=True),
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
            obj_controls=(
                Controls(timestamp=4.0, ability_1=True),
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