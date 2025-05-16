from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.handlers.id_gen import IdGen
from src.models.game_obj import GameObj
from src.models.spell import SpellFlag, Spell
from src.handlers.event_log import EventLog
from src.handlers.controls_handler import ControlsHandler


class GameObjHandler:

    def __init__(self) -> None:
        self._game_objs: Dict[int, GameObj] = {}
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self.setup_spell_id: int = IdGen.EMPTY_ID
        self.environment_id: int = IdGen.EMPTY_ID
        self.player_id: int = IdGen.EMPTY_ID
        self.boss1_id: int = IdGen.EMPTY_ID
        self.boss2_id: int = IdGen.EMPTY_ID

    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.values()

    def generate_new_game_obj_id(self) -> int:
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
        self.setup_spell_id = setup_spell_id
        assert IdGen.is_empty_id(self.environment_id), f"Environment is already initialized (ID={self.environment_id})"
        game_obj = GameObj.create_environment(self.generate_new_game_obj_id())
        self.add_game_obj(game_obj)
        self.environment_id = game_obj.obj_id

    def handle_spawn(self, source_obj: GameObj, spell: Spell, all_controls: ControlsHandler) -> None:
        if spell.spawned_obj is not None:
            obj_id = self.generate_new_game_obj_id()
            new_obj = GameObj.create_from_template(obj_id, source_obj.obj_id, spell.spawned_obj)
            self.add_game_obj(new_obj)
            if spell.obj_controls is not None:
                for controls in spell.obj_controls:
                    all_controls.add_controls(obj_id, controls.timestamp, controls)
            if spell.flags & SpellFlag.SPAWN_BOSS:
                if IdGen.is_empty_id(self.boss1_id):
                    self.boss1_id = new_obj.obj_id
                else:
                    assert IdGen.is_empty_id(self.boss2_id), "Second boss already exists."
                    self.boss2_id = new_obj.obj_id
            if spell.flags & SpellFlag.SPAWN_PLAYER:
                assert IdGen.is_empty_id(self.player_id), "Player already exists."
                self.player_id = new_obj.obj_id
