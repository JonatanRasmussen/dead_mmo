from typing import List, Tuple, NamedTuple, Optional, Iterable
import math

from src.config import Colors, Consts
from .controls import Controls
from .obj_status import ObjStatus
from .upcoming_event import UpcomingEvent


# Brainstorm for components:
    # DefaultIDs
    # Delays
    # Health
    # HitChance
    # Items
    # Keybindings
    # Limitations
    # Logger
    # Lockout
    # Movement
    # Modifiers
    # PassiveEffects
    # Position
    # Power
    # Progress
    # Quests
    # Randomness
    # Resistances
    # Resource
    # RpgStats
    # Visuals
    # Waits
    # Weights

class GameObj(NamedTuple):
    """ Combat units. Controlled by the player or NPCs. """
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell: int = Consts.EMPTY_ID

    # Status effects
    status: ObjStatus = ObjStatus.NONE

    # Targeting
    is_allied: bool = False
    current_target: int = Consts.EMPTY_ID
    selected_spell: int = Consts.EMPTY_ID

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
    start_move_up_id: int = Consts.EMPTY_ID
    stop_move_up_id: int = Consts.EMPTY_ID
    start_move_left_id: int = Consts.EMPTY_ID
    stop_move_left_id: int = Consts.EMPTY_ID
    start_move_down_id: int = Consts.EMPTY_ID
    stop_move_down_id: int = Consts.EMPTY_ID
    start_move_right_id: int = Consts.EMPTY_ID
    stop_move_right_id: int = Consts.EMPTY_ID

    # Ability spell slots
    next_target_id: int = Consts.EMPTY_ID
    ability_1_id: int = Consts.EMPTY_ID
    ability_2_id: int = Consts.EMPTY_ID
    ability_3_id: int = Consts.EMPTY_ID
    ability_4_id: int = Consts.EMPTY_ID

    # Cooldown timestamps
    spawn_timestamp: float = Consts.EMPTY_TIMESTAMP
    gcd_start: float = Consts.EMPTY_TIMESTAMP
    ability_1_cd_start: float = Consts.EMPTY_TIMESTAMP
    ability_2_cd_start: float = Consts.EMPTY_TIMESTAMP
    ability_3_cd_start: float = Consts.EMPTY_TIMESTAMP
    ability_4_cd_start: float = Consts.EMPTY_TIMESTAMP

    # Appearance
    color: Tuple[int, int, int] = Colors.WHITE

    # Cosmetics
    sprite_name: str = ""
    audio_name: str = ""

    @property
    def should_play_audio(self) -> bool:
        return self.audio_name is not None and self.audio_name != ""

    @property
    def should_render_sprite(self) -> bool:
        return self.sprite_name is not None and self.sprite_name != "" and self.is_visible

    @property
    def size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self.hp))

    @property
    def spell_modifier(self) -> float:
        return 1.0

    @property
    def is_environment(self) -> float:
        return self.status in {ObjStatus.ENVIRONMENT}

    @property
    def is_visible(self) -> bool:
        return not self.status in {ObjStatus.ENVIRONMENT, ObjStatus.DESPAWNED}

    @property
    def is_despawned(self) -> bool:
        return self.status == ObjStatus.DESPAWNED


    @classmethod
    def create_environment(cls, obj_id: int) -> 'GameObj':
        return GameObj(obj_id=obj_id, status=ObjStatus.ENVIRONMENT, current_target=obj_id)

    def create_child_obj(self, obj_id: int, parent: 'GameObj', timestamp: float, target_id: int) -> 'GameObj':
        if parent.is_environment:
            team = self.is_allied
        else:
            team = parent.is_allied
        return self._replace(
            obj_id=obj_id,
            parent_id=parent.obj_id,
            spawn_timestamp=timestamp,
            current_target=target_id,
            status=ObjStatus.ALIVE,
            is_allied=team,
            x=parent.x+self.x,
            y=parent.y+self.y,
        )

    def get_gcd_progress(self, current_time: float) -> float:
        return min(1.0, (current_time - self.gcd_start) / self.gcd)

    def change_status(self, new_status: ObjStatus) -> 'GameObj':
        return self._replace(status=new_status)

    def teleport_to(self, new_x: float, new_y: float) -> 'GameObj':
        return self._replace(x=new_x, y=new_y)

    def teleport_to_coordinates(self, new_x: float, new_y: float) -> 'GameObj':
        return self._replace(x=new_x, y=new_y)

    def move_in_direction(self, x: float, y: float, move_speed: float) -> 'GameObj':
        GLOBAL_MODIFIER = Consts.MOVEMENT_DISTANCE_PER_SECOND / Consts.MOVEMENT_UPDATES_PER_SECOND
        new_x = self.x + x * move_speed * GLOBAL_MODIFIER
        new_y = self.y + y * move_speed * GLOBAL_MODIFIER
        return self.teleport_to_coordinates(new_x, new_y)

    def move_towards_coordinates(self, x: float, y: float, move_speed: float) -> 'GameObj':
        dx = x - self.x
        dy = y - self.y
        distance = math.hypot(dx, dy)
        if distance == 0:
            return self
        return self.move_in_direction(dx/distance, dy/distance, move_speed)

    def set_ability_1(self, new_ability_1: int) -> 'GameObj':
        return self._replace(ability_1_id=new_ability_1)

    def set_ability_2(self, new_ability_2: int) -> 'GameObj':
        return self._replace(ability_2_id=new_ability_2)

    def set_ability_3(self, new_ability_3: int) -> 'GameObj':
        return self._replace(ability_3_id=new_ability_3)

    def set_ability_4(self, new_ability_4: int) -> 'GameObj':
        return self._replace(ability_4_id=new_ability_4)

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

    def is_same_team(self, other: 'GameObj') -> bool:
        return self.is_allied == other.is_allied

    def print_delta(self, other: 'GameObj') -> None:
        # Convert to dictionaries
        d1, d2 = self._asdict(), other._asdict()
        diff = {key: (d1[key], d2[key]) for key in d1 if d1[key] != d2[key]}
        print(diff)

    def create_events_from_controls(self, controls: Controls, frame_start: float, frame_end: float) -> Iterable[UpcomingEvent]:
        if not self.is_despawned and frame_start < controls.ingame_timestamp <= frame_end:
            spell_ids = self._convert_controls_to_spell_ids(controls)
            input_event_order = 0
            for spell_id in spell_ids:
                input_event_order += 1
                yield UpcomingEvent(
                    timestamp=controls.ingame_timestamp,
                    source_id=self.obj_id,
                    spell_id=spell_id,
                    target_id=self.current_target,
                    priority=input_event_order,
                )

    def _convert_controls_to_spell_ids(self, controls: Controls) -> List[int]:
        spell_ids: List[int] = []
        if controls.start_move_up:
            assert Consts.is_valid_id(self.start_move_up_id), f"Invalid spell ID for {self.obj_id}: start_move_up_id"
            spell_ids.append(self.start_move_up_id)
        if controls.stop_move_up:
            assert Consts.is_valid_id(self.stop_move_up_id), f"Invalid spell ID for {self.obj_id}: stop_move_up_id"
            spell_ids.append(self.stop_move_up_id)
        if controls.start_move_left:
            assert Consts.is_valid_id(self.start_move_left_id), f"Invalid spell ID for {self.obj_id}: start_move_left_id"
            spell_ids.append(self.start_move_left_id)
        if controls.stop_move_left:
            assert Consts.is_valid_id(self.stop_move_left_id), f"Invalid spell ID for {self.obj_id}: stop_move_left_id"
            spell_ids.append(self.stop_move_left_id)
        if controls.start_move_down:
            assert Consts.is_valid_id(self.start_move_down_id), f"Invalid spell ID for {self.obj_id}: start_move_down_id"
            spell_ids.append(self.start_move_down_id)
        if controls.stop_move_down:
            assert Consts.is_valid_id(self.stop_move_down_id), f"Invalid spell ID for {self.obj_id}: stop_move_down_id"
            spell_ids.append(self.stop_move_down_id)
        if controls.start_move_right:
            assert Consts.is_valid_id(self.start_move_right_id), f"Invalid spell ID for {self.obj_id}: start_move_right_id"
            spell_ids.append(self.start_move_right_id)
        if controls.stop_move_right:
            assert Consts.is_valid_id(self.stop_move_right_id), f"Invalid spell ID for {self.obj_id}: stop_move_right_id"
            spell_ids.append(self.stop_move_right_id)
        if controls.swap_target:
            assert Consts.is_valid_id(self.next_target_id), f"Invalid spell ID for {self.obj_id}: next_target_id"
            spell_ids.append(self.next_target_id)
        if controls.ability_1:
            assert Consts.is_valid_id(self.ability_1_id), f"Invalid spell ID for {self.obj_id}: ability_1_id"
            spell_ids.append(self.ability_1_id)
        if controls.ability_2:
            assert Consts.is_valid_id(self.ability_2_id), f"Invalid spell ID for {self.obj_id}: ability_2_id"
            spell_ids.append(self.ability_2_id)
        if controls.ability_3:
            assert Consts.is_valid_id(self.ability_3_id), f"Invalid spell ID for {self.obj_id}: ability_3_id"
            spell_ids.append(self.ability_3_id)
        if controls.ability_4:
            assert Consts.is_valid_id(self.ability_4_id), f"Invalid spell ID for {self.obj_id}: ability_4_id"
            spell_ids.append(self.ability_4_id)
        assert not controls.is_empty, f"Controls for {self.obj_id} is empty."
        assert Consts.EMPTY_ID not in spell_ids, f"Controls for {self.obj_id} is casting empty spell ID, fix spell configs."
        return spell_ids
