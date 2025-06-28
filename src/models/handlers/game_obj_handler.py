from typing import Dict, List, Tuple, Iterable, ValuesView, Optional

from src.models.components import ImportantIDs, Behavior, GameObj, FinalizedEvent
from src.models.services import EventLog, IdGen


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

    def _generate_new_game_obj_id(self) -> int:
        return self._game_obj_id_gen.generate_new_id()

    def has_game_obj(self, obj_id: int) -> bool:
        return obj_id in self._game_objs

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

    def initialize_environment(self) -> None:
        assert not self._important_ids.environment_exists, f"Environment is already initialized (ID={self._important_ids.environment_id})"
        game_obj = GameObj.create_environment(self._generate_new_game_obj_id())
        self.add_game_obj(game_obj)
        self._important_ids = self._important_ids.initialize_environment(game_obj.obj_id)

    def modify_game_obj(self, f_event: FinalizedEvent) -> None:
        spell = f_event.spell
        if spell.is_modifying_source:
            updated_source_obj = spell.flags.modify_source(f_event.timestamp, f_event.source, f_event.target)
            self.update_game_obj(updated_source_obj)
        else:
            updated_source_obj = f_event.source
        if updated_source_obj.obj_id == f_event.target_id:
            target_obj = updated_source_obj  # Do not overwrite changes made to updated_source_obj
        else:
            target_obj = f_event.target
        updated_target_obj = spell.flags.modify_target(updated_source_obj, spell.power, spell.external_spell, target_obj)
        self.update_game_obj(updated_target_obj)

    def handle_spawn(self, f_event: FinalizedEvent) -> Optional[GameObj]:
        timestamp = f_event.timestamp
        spell = f_event.spell
        parent_obj = f_event.source
        if spell.spawned_obj is None:
            return None
        obj_id = self._generate_new_game_obj_id()
        new_obj = spell.spawned_obj.create_child_obj(obj_id, parent_obj, timestamp, f_event.target.obj_id)
        self.add_game_obj(new_obj)
        if spell.flags & Behavior.SPAWN_BOSS:
            if not self._important_ids.boss1_exists:
                self._important_ids = self._important_ids.update_boss1_id(new_obj.obj_id)
            else:
                assert not self._important_ids.boss2_exists, "Second boss already exists."
                self._important_ids = self._important_ids.update_boss2_id(new_obj.obj_id)
        if spell.flags & Behavior.SPAWN_PLAYER:
            assert not self._important_ids.player_exists, "Player already exists."
            self._important_ids = self._important_ids.update_player_id(new_obj.obj_id)
        return new_obj

    def _game_obj_is_environment(self, game_obj: GameObj) -> bool:
        return game_obj.obj_id == self._important_ids.environment_id
