from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.handlers.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.important_ids import ImportantIDs
from src.models.spell import SpellFlag, Spell
from src.handlers.event_log import EventLog
from src.utils.spell_resolving import SpellResolving


class GameObjHandler:

    def __init__(self) -> None:
        self._game_objs: Dict[int, GameObj] = {}
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._important_ids: ImportantIDs = ImportantIDs()

    @property
    def important_ids(self) -> ImportantIDs:
        return self._important_ids

    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.values()

    @property
    def get_lowest_and_highest_game_obj_id(self) -> Tuple[int, int]:
        min_id = min(self._game_objs.keys()) if self._game_objs else 0
        max_id = max(self._game_objs.keys()) if self._game_objs else 0
        return (min_id, max_id)

    def _generate_new_game_obj_id(self) -> int:
        return self._game_obj_id_gen.generate_new_id()

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self._game_objs, f"GameObj with ID {obj_id} does not exist."
        return self._game_objs.get(obj_id, GameObj())

    def add_game_obj(self, game_obj: GameObj) -> None:
        if EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            EventLog.summarize_new_obj_creation(game_obj)
        assert game_obj.obj_id not in self._game_objs, f"GameObj with ID {game_obj.obj_id} already exists."
        self._game_objs[game_obj.obj_id] = game_obj

    def update_game_obj(self, updated_game_obj: GameObj) -> None:
        if EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            pre_update_obj = self.get_game_obj(updated_game_obj.obj_id)
            EventLog.summarize_state_update(pre_update_obj, updated_game_obj)
        assert updated_game_obj.obj_id in self._game_objs, f"GameObj with ID {updated_game_obj.obj_id} does not exist."
        self._game_objs[updated_game_obj.obj_id] = updated_game_obj

    def initialize_root_environment_obj(self, setup_spell_id: int) -> None:
        self._important_ids = self._important_ids.update_setup_spell_id(setup_spell_id)
        assert not self._important_ids.environment_exists, f"Environment is already initialized (ID={self._important_ids.environment_id})"
        game_obj = GameObj.create_environment(self._generate_new_game_obj_id())
        self.add_game_obj(game_obj)
        self._important_ids = self._important_ids.update_environment_id(game_obj.obj_id)

    def modify_game_obj(self, timestamp: float, source_obj: GameObj, spell: Spell, target_obj: GameObj) -> None:
        if spell.is_modifying_source:
            updated_source_obj = SpellResolving.modify_source(timestamp, source_obj, spell)
            self.update_game_obj(updated_source_obj)
        else:
            updated_source_obj = source_obj
        updated_target_obj = SpellResolving.modify_target(updated_source_obj, spell, target_obj, self._important_ids)
        self.update_game_obj(updated_target_obj)

    def handle_spawn(self, source_obj: GameObj, spell: Spell) -> int:
        if spell.spawned_obj is None:
            return IdGen.EMPTY_ID
        obj_id = self._generate_new_game_obj_id()
        new_obj = GameObj.create_from_template(obj_id, source_obj.obj_id, spell.spawned_obj)
        self.add_game_obj(new_obj)
        if spell.flags & SpellFlag.SPAWN_BOSS:
            if not self._important_ids.boss1_exists:
                self._important_ids = self._important_ids.update_boss1_id(new_obj.obj_id)
            else:
                assert not self._important_ids.boss2_exists, "Second boss already exists."
                self._important_ids = self._important_ids.update_boss2_id(new_obj.obj_id)
        if spell.flags & SpellFlag.SPAWN_PLAYER:
            assert not self._important_ids.player_exists, "Player already exists."
            self._important_ids = self._important_ids.update_player_id(new_obj.obj_id)
        return obj_id