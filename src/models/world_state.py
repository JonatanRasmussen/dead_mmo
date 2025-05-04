from sortedcontainers import SortedDict  # type: ignore
from typing import Dict, List, Tuple

from src.models.id_gen import IdGen
from src.models.controls import Controls
from src.models.game_obj import GameObj
from src.models.spell import Spell
from src.models.aura import Aura
from src.config.spell_db import SpellDatabase


class WorldState:
    """ The entire game state of the save file that is currently in use """
    def __init__(self) -> None:
        self.previous_timestamp: float = 0.0
        self.current_timestamp: float = 0.0

        self.game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self.environment: GameObj = GameObj(obj_id=self.game_obj_id_gen.new_id())
        self.player_id: int = IdGen.EMPTY_ID
        self.boss1_id: int = IdGen.EMPTY_ID
        self.boss2_id: int = IdGen.EMPTY_ID

        self.auras: SortedDict[Tuple[int, int, int], Aura] = SortedDict()
        self.controls: SortedDict[Tuple[float, int], Controls] = SortedDict()
        self.game_objs: Dict[int, GameObj] = {self.environment.obj_id: self.environment}
        self.spell_database: SpellDatabase = SpellDatabase()

    @property
    def delta_time(self) -> float:
        return self.current_timestamp - self.previous_timestamp
    @property
    def player_exists(self) -> float:
        return not IdGen.is_empty_id(self.player_id)
    @property
    def boss1_exists(self) -> float:
        return not IdGen.is_empty_id(self.boss1_id)
    @property
    def boss2_exists(self) -> float:
        return not IdGen.is_empty_id(self.boss2_id)

    def advance_timestamp(self, delta_time: float) -> None:
        self.previous_timestamp = self.current_timestamp
        self.current_timestamp += delta_time

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self.game_objs, f"GameObj with ID {obj_id} does not exist."
        return self.game_objs.get(obj_id, GameObj())

    def update_game_obj(self, updated_game_obj: GameObj) -> None:
        assert updated_game_obj.obj_id in self.game_objs, f"GameObj with ID {updated_game_obj.obj_id} does not exist."
        self.game_objs[updated_game_obj.obj_id] = updated_game_obj

    def add_game_obj(self, game_obj: GameObj) -> None:
        assert game_obj.obj_id not in self.game_objs, f"GameObj with ID {game_obj.obj_id} already exists."
        self.game_objs[game_obj.obj_id] = game_obj

    def add_controls(self, obj_id: int, timestamp: float, new_controls: Controls) -> None:
        key: Tuple[float, int] = (timestamp, obj_id)
        assert key not in self.controls, f"Controls with (timestamp, obj_id) = ({key}) already exists."
        self.controls[key] = new_controls

    def add_player_controls(self, player_controls: Controls) -> None:
        if self.player_exists:
            self.add_controls(self.player_id, self.current_timestamp, player_controls)

    def add_aura(self, source_id: int, spell: Spell, target_id: int) -> None:
        aura = Aura.create_from_spell(self.current_timestamp, source_id, spell, target_id)
        key: Tuple[int, int, int] = aura.aura_id
        assert key not in self.auras, f"Aura with (source, spell, target) = ({key}) already exists."
        self.auras[key] = aura

    def get_aura(self, aura_id: Tuple[int, int, int]) -> Aura:
        key = aura_id
        assert key in self.auras, f"Aura with ID ({aura_id}) does not exist."
        return self.auras.get(key, Aura())

    def get_obj_auras(self, obj_id: int) -> List[Aura]:
        return [aura for aura in self.auras.values() if aura.target_id == obj_id]
