from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple, ValuesView

from src.models.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import Spell
from src.models.aura import Aura
from src.config.spell_db import SpellDatabase


class WorldState:
    """ The entire game state of the save file that is currently in use """
    def __init__(self) -> None:
        self._previous_timestamp: float = 0.0
        self._current_timestamp: float = 0.0

        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self._setup_spell_id: int = IdGen.EMPTY_ID
        self._environment_id: int = IdGen.EMPTY_ID
        self._player_id: int = IdGen.EMPTY_ID
        self._boss1_id: int = IdGen.EMPTY_ID
        self._boss2_id: int = IdGen.EMPTY_ID

        self._auras: SortedDict[Tuple[int, int, int], Aura] = SortedDict()
        self._controls: SortedDict[Tuple[float, int], Controls] = SortedDict()
        self._game_objs: Dict[int, GameObj] = {}
        self._spell_database: SpellDatabase = SpellDatabase()

    @property
    def previous_timestamp(self) -> float:
        return self._previous_timestamp
    @property
    def current_timestamp(self) -> float:
        return self._current_timestamp
    @property
    def delta_time(self) -> float:
        return self._current_timestamp - self._previous_timestamp

    @property
    def all_auras(self) -> ValuesView[Aura]:
        return self._auras.values()
    @property
    def all_controls(self) -> ValuesView[Controls]:
        return self._controls.values()
    @property
    def all_controls_in_current_frame(self) -> List[Tuple[float, int, Controls]]:
        return self.get_controls_in_timerange(self.previous_timestamp, self.current_timestamp)
    @property
    def all_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.values()
    @property
    def spell_database(self) -> SpellDatabase:
        return self._spell_database

    @property
    def setup_spell_id(self) -> int:
        return self._setup_spell_id
    @property
    def environment_id(self) -> int:
        return self._environment_id
    @property
    def player_id(self) -> int:
        return self._player_id
    @property
    def boss1_id(self) -> int:
        return self._boss1_id
    @property
    def boss2_id(self) -> int:
        return self._boss2_id

    @property
    def has_been_initialized(self) -> bool:
        return self.player_exists
    @property
    def setup_spell_id_exists(self) -> bool:
        return not IdGen.is_empty_id(self._setup_spell_id)
    @property
    def environment_exists(self) -> bool:
        return not IdGen.is_empty_id(self._environment_id)
    @property
    def player_exists(self) -> bool:
        return not IdGen.is_empty_id(self._player_id)
    @property
    def boss1_exists(self) -> bool:
        return not IdGen.is_empty_id(self._boss1_id)
    @property
    def boss2_exists(self) -> bool:
        return not IdGen.is_empty_id(self._boss2_id)

    def advance_timestamp(self, delta_time: float) -> None:
        self._previous_timestamp = self._current_timestamp
        self._current_timestamp += delta_time

    def generate_new_event_id(self) -> int:
        return self._event_id_gen.new_id()

    def generate_new_game_obj_id(self) -> int:
        return self._game_obj_id_gen.new_id()

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self._game_objs, f"GameObj with ID {obj_id} does not exist."
        return self._game_objs.get(obj_id, GameObj())

    def add_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self._game_objs, f"GameObj with ID {game_obj.obj_id} already exists."
        self._game_objs[game_obj.obj_id] = game_obj

    def update_game_obj(self, updated_game_obj: GameObj) -> None:
        assert updated_game_obj.obj_id in self._game_objs, f"GameObj with ID {updated_game_obj.obj_id} does not exist."
        self._game_objs[updated_game_obj.obj_id] = updated_game_obj

    def get_controls(self, timestamp: float, obj_id: int) -> Controls:
        controls_key: Tuple[float, int] = (timestamp, obj_id)
        assert controls_key in self._controls, f"Controls with ID {controls_key} does not exist."
        return self._controls.get(controls_key, Controls())

    def get_controls_in_timerange(self, prev_t: float, curr_t: float) -> List[Tuple[float, int, Controls]]:
        start_key = (prev_t, min(self._game_objs.keys()) if self._game_objs else 0)
        end_key = (curr_t, max(self._game_objs.keys()) if self._game_objs else 0)
        return [(k[0], k[1], self._controls[k]) for k in self._controls.irange(start_key, end_key)]

    def add_controls(self, obj_id: int, timestamp: float, new_controls: Controls) -> None:
        key: Tuple[float, int] = (timestamp, obj_id)
        assert key not in self._controls, f"Controls with (timestamp, obj_id) = ({key}) already exists."
        self._controls[key] = new_controls

    def add_player_controls(self, player_controls: Controls) -> None:
        if self.player_exists:
            self.add_controls(self._player_id, self._current_timestamp, player_controls)

    def add_aura(self, source_id: int, spell: Spell, target_id: int) -> None:
        aura = Aura.create_from_spell(self._current_timestamp, source_id, spell, target_id)
        key: Tuple[int, int, int] = aura.aura_id
        assert key not in self._auras, f"Aura with (source, spell, target) = ({key}) already exists."
        self._auras[key] = aura

    def get_aura(self, source_id: int, spell_id: int, target_id: int) -> Aura:
        key: Tuple[int, int, int] = (source_id, spell_id, target_id)
        assert key in self._auras, f"Aura with ID {key} does not exist."
        return self._auras.get(key, Aura())

    def get_obj_auras(self, obj_id: int) -> List[Aura]:
        return [aura for aura in self._auras.values() if aura.target_id == obj_id]

    def modify_setup_spell_id(self, setup_spell_id: int) -> None:
        self._setup_spell_id = setup_spell_id
        self.initialize_environment()

    def initialize_environment(self) -> None:
        assert not self.environment_exists, f"Environment is already initialized (ID={self.environment_id})"
        game_obj = GameObj.create_environment(self._game_obj_id_gen.new_id())
        self.add_game_obj(game_obj)
        self._environment_id = game_obj.obj_id

    def update_player_id(self, new_id: int) -> None:
        self._player_id = new_id

    def update_boss1_id(self, new_id: int) -> None:
        self._boss1_id = new_id

    def update_boss2_id(self, new_id: int) -> None:
        self._boss2_id = new_id