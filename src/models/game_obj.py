from typing import List, Tuple, NamedTuple
from enum import Enum, auto
import math

from src.config.color import Color
from src.handlers.id_gen import IdGen
from src.models.controls import Controls


class GameObjStatus(Enum):
    """ Flags for various status effects of game objects. """
    NONE = 0
    CASTING = auto()
    CHANNELING = auto()
    CROWD_CONTROLLED = auto()
    BANISHED = auto()


class GameObj(NamedTuple):
    """ Combat units. Controlled by the player or NPCs. """
    obj_id: int = IdGen.EMPTY_ID
    parent_id: int = IdGen.EMPTY_ID
    spawned_from_spell: int = IdGen.EMPTY_ID

    # Appearance
    color: Tuple[int, int, int] = Color.WHITE

    # Status effects
    statuses: GameObjStatus = GameObjStatus.NONE

    # Targeting
    is_allied: bool = False
    current_target: int = IdGen.EMPTY_ID
    selected_spell: int = IdGen.EMPTY_ID

    # Combat stats
    hp: float = 0.0
    movement_speed: float = 1.0
    is_attackable: bool = False
    is_player: bool = False
    gcd: float = 1.0

    # Positional data
    x: float = 0.0
    y: float = 0.0
    angle: float = 0.0

    # Ability movement slots
    start_move_up_id: int = IdGen.EMPTY_ID
    stop_move_up_id: int = IdGen.EMPTY_ID
    start_move_left_id: int = IdGen.EMPTY_ID
    stop_move_left_id: int = IdGen.EMPTY_ID
    start_move_down_id: int = IdGen.EMPTY_ID
    stop_move_down_id: int = IdGen.EMPTY_ID
    start_move_right_id: int = IdGen.EMPTY_ID
    stop_move_right_id: int = IdGen.EMPTY_ID

    # Ability spell slots
    next_target_id: int = IdGen.EMPTY_ID
    ability_1_id: int = IdGen.EMPTY_ID
    ability_2_id: int = IdGen.EMPTY_ID
    ability_3_id: int = IdGen.EMPTY_ID
    ability_4_id: int = IdGen.EMPTY_ID

    # Cooldown timestamps
    spawn_timestamp: float = 0.0
    gcd_start: float = 0.0
    ability_1_cd_start: float = 0.0
    ability_2_cd_start: float = 0.0
    ability_3_cd_start: float = 0.0
    ability_4_cd_start: float = 0.0


    @property
    def size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self.hp))

    @property
    def spell_modifier(self) -> float:
        return 1.0

    @property
    def gcd_progress(self) -> float:
        return min(1.0, (0 - self.gcd_start) / self.gcd)

    @classmethod
    def create_from_template(cls, unique_obj_id: int, parent_id: int, other: 'GameObj') -> 'GameObj':
        return other._replace(obj_id=unique_obj_id, parent_id=parent_id)

    @classmethod
    def create_environment(cls, unique_obj_id: int) -> 'GameObj':
        return GameObj(obj_id=unique_obj_id)

    def teleport_to(self, new_x: float, new_y: float) -> 'GameObj':
        return self._replace(x=new_x, y=new_y)

    def move_in_direction(self, x: float, y: float, move_speed: float, delta_t: float) -> 'GameObj':
        new_x = self.x + x * move_speed * delta_t
        new_y = self.y + y * move_speed * delta_t
        return self._replace(x=new_x, y=new_y)

    def switch_target(self, new_target: int) -> 'GameObj':
        return self._replace(current_target=new_target)

    def suffer_damage(self, spell_power: float) -> 'GameObj':
        return self._replace(hp=self.hp - spell_power)

    def restore_health(self, spell_power: float) -> 'GameObj':
        return self._replace(hp=self.hp + spell_power)

    def set_gcd_start(self, new_gcd_start: float) -> 'GameObj':
        return self._replace(gcd_start=new_gcd_start)

    def get_time_since_spawn(self, current_time: float) -> float:
        return current_time - self.spawn_timestamp

    def print_delta(self, other: 'GameObj') -> None:
        # Convert to dictionaries
        d1, d2 = self._asdict(), other._asdict()
        diff = {key: (d1[key], d2[key]) for key in d1 if d1[key] != d2[key]}
        print(diff)

    def convert_controls_to_spell_ids(self, controls: Controls) -> List[int]:
        spell_ids: List[int] = []
        spell_ids += [self.start_move_up_id] if controls.start_move_up else []
        spell_ids += [self.stop_move_up_id] if controls.stop_move_up else []
        spell_ids += [self.start_move_left_id] if controls.start_move_left else []
        spell_ids += [self.stop_move_left_id] if controls.stop_move_left else []
        spell_ids += [self.start_move_down_id] if controls.start_move_down else []
        spell_ids += [self.stop_move_down_id] if controls.stop_move_down else []
        spell_ids += [self.start_move_right_id] if controls.start_move_right else []
        spell_ids += [self.stop_move_right_id] if controls.stop_move_right else []
        spell_ids += [self.next_target_id] if controls.next_target else []
        spell_ids += [self.ability_1_id] if controls.ability_1 else []
        spell_ids += [self.ability_2_id] if controls.ability_2 else []
        spell_ids += [self.ability_3_id] if controls.ability_3 else []
        spell_ids += [self.ability_4_id] if controls.ability_4 else []
        assert IdGen.EMPTY_ID not in spell_ids, f"Controls has empty spell cast: {self}{controls}"
        return spell_ids
