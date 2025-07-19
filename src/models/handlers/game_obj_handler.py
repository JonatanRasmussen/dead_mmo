from typing import ValuesView, Optional

from src.models.components import GameObj, Status
from src.models.data import Behavior, DefaultIDs, Spell
from src.models.events import FinalizedEvent
from src.models.handlers.event_log import EventLog
from src.models.handlers.id_gen import IdGen


class GameObjHandler:

    def __init__(self) -> None:
        self._game_objs: dict[int, GameObj] = {}
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._default_ids: DefaultIDs = DefaultIDs()
        self._create_environment_obj()

    @property
    def default_ids(self) -> DefaultIDs:
        return self._default_ids

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

    def modify_game_obj(self, f_event: FinalizedEvent) -> None:
        spell = f_event.spell
        spell.flags.modify_source(f_event.timestamp, f_event.source, f_event.target)
        spell.flags.modify_target(f_event.source, spell.power, f_event.target)

    def handle_spawn(self, f_event: FinalizedEvent) -> Optional[GameObj]:
        template = f_event.spell.spawned_obj
        if template is None:
            return None
        new_obj_id = self._generate_new_game_obj_id()
        child = template.create_child(new_obj_id, f_event.source, f_event.timestamp, f_event.target_id)
        self.add_game_obj(child)
        self._update_default_ids(child, f_event.spell)
        return child

    def _create_environment_obj(self) -> None:
        assert not self.default_ids.environment_exists, f"Environment is already initialized (ID={self._default_ids.environment_id})"
        game_obj = GameObj.create_environment(self._generate_new_game_obj_id())
        self.add_game_obj(game_obj)
        self.default_ids.environment_id = game_obj.obj_id

    def _update_default_ids(self, new_obj: GameObj, spell: Spell) -> None:
        if spell.flags & Behavior.SPAWN_BOSS:
            if not self._default_ids.boss1_exists:
                self._default_ids.boss1_id = new_obj.obj_id
            else:
                assert not self._default_ids.boss2_exists, "Second boss already exists."
                self._default_ids.boss2_id = new_obj.obj_id
        if spell.flags & Behavior.SPAWN_PLAYER:
            assert not self._default_ids.player_exists, "Player already exists."
            self._default_ids.player_id = new_obj.obj_id