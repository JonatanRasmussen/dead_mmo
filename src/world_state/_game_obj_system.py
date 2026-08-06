import json
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Iterable, Optional
from enum import Enum, auto
from src.utils import CopyTools


from src.settings import Colors, Consts
from src.world_state import Controls, KeyPresses, Loadout

class Distance(float):
    def __new__(cls, value: float) -> 'Distance':
        return super().__new__(cls, value)

    def __add__(self, other: float) -> 'Distance':
        return Distance(super().__add__(other))

    def __sub__(self, other: float) -> 'Distance':
        return Distance(super().__sub__(other))

    def __mul__(self, other: float) -> 'Distance':
        return Distance(super().__mul__(other))

    def __truediv__(self, other: float) -> 'Distance':
        return Distance(super().__truediv__(other))

@dataclass(slots=True)
class Position:
    """Positional data for GameObjs"""
    x: Distance = Distance(0.0)
    y: Distance = Distance(0.0)
    angle: float = 0.0
    movement_speed: float = 1.0
    base_size: float = 1.0

    @classmethod
    def deserialize(cls, data: str) -> 'Position':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            x=Distance(d["x"]),
            y=Distance(d["y"]),
            angle=d["a"],
            movement_speed=d["ms"],
            base_size=d["bs"]
        )
    def serialize(self) -> str:
        return json.dumps(
            {
                "x": self.x,
                "y": self.y,
                "a": self.angle,
                "ms": self.movement_speed,
                "bs": self.base_size
            }
        )

    @classmethod
    def create_at(cls, x: float, y: float) -> 'Position':
        return Position(x=Distance(x), y=Distance(y))

    def has_target_within_range(self, target: 'Position', range_limit: float) -> bool:
        dx = self.x - target.x
        dy = self.y - target.y
        return dx * dx + dy * dy <= range_limit * range_limit

    def teleport_to_position(self, new_pos: 'Position') -> None:
        self.x = new_pos.x
        self.y = new_pos.y

    def move_in_direction(self, direction: 'Position', move_speed: float) -> None:
        GLOBAL_MODIFIER = Consts.MOVEMENT_DISTANCE_PER_SECOND / Consts.MOVEMENT_UPDATES_PER_SECOND
        new_x = self.x + direction.x * move_speed * GLOBAL_MODIFIER
        new_y = self.y + direction.y * move_speed * GLOBAL_MODIFIER
        self.teleport_to_position(Position(new_x, new_y))

    def move_up(self, move_speed: float) -> None:
        up = Position.create_at(0.0, 1.0)
        self.move_in_direction(up, move_speed)

    def move_left(self, move_speed: float) -> None:
        left = Position.create_at(-1.0, 0.0)
        self.move_in_direction(left, move_speed)

    def move_down(self, move_speed: float) -> None:
        down = Position.create_at(0.0, -1.0)
        self.move_in_direction(down, move_speed)

    def move_right(self, move_speed: float) -> None:
        right = Position.create_at(1.0, 0.0)
        self.move_in_direction(right, move_speed)

    def move_towards_destination(self, destination: 'Position', move_speed: float) -> None:
        dx = destination.x - self.x
        dy = destination.y - self.y
        distance = math.hypot(dx, dy)
        if not distance == 0.0:
            direction = Position(dx / distance, dy / distance)
            self.move_in_direction(direction, move_speed)

class Faction(Enum):
    """ Team relationships between GameObjs, used for spell targeting. """
    EMPTY = 0
    ALLIED = auto()
    ENEMY = auto()

    @property
    def is_allied(self) -> bool:
        return self in {Faction.ALLIED}

    @property
    def is_enemy(self) -> bool:
        return self in {Faction.ENEMY}

    def is_valid_aoe_target(self, sources_team: 'Faction', targets_team: 'Faction') -> bool:
        return (self == sources_team) == (sources_team == targets_team)

@dataclass(slots=True)
class Resources:
    """ Resources used by GameObjs such as health, mana and spell charges. """
    hp: float = 0.0
    team: Faction = Faction.EMPTY

    @classmethod
    def deserialize(cls, data: str) -> 'Resources':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            hp=d["hp"],
            team=Faction(d["tm"])
        )
    def serialize(self) -> str:
        return json.dumps({
            "hp": self.hp,
            "tm": self.team.value
        })


class Status(Enum):
    """ Various status effects that game objects can have. """
    EMPTY = 0  # Should never be used outside initialization
    ENVIRONMENT = auto()  # Special case used only by ENVIRONMENT objs
    NEW_PLAYER_OBJ = auto()  # Special case used temporarily by newly spawned players
    NEW_BOSS_OBJ = auto()  # Special case used temporarily by newly spawned bosses
    ALIVE = auto()  # Default status used to indicate the absence of other status effects
    INACTIVE = auto()  # Not yet engaged in combat, cannot be source or target of events
    DESPAWNED = auto()  # Permamently removed from combat, cannot be source or target of events
    BANISHED = auto()  # Temporarily removed from combat, cannot be source or target of events
    CASTING = auto()  # to-do: document this
    CHANNELING = auto()  # to-do: document this
    ROOTED = auto()  # to-do: document this
    STUNNED = auto()  # to-do: document this

    @property
    def is_valid_source(self) -> bool:
        return not self in {
            Status.DESPAWNED,
            Status.BANISHED,
        }

    @property
    def is_valid_target(self) -> bool:
        return not self in {
            Status.ENVIRONMENT,
            Status.DESPAWNED,
            Status.BANISHED,
        }


@dataclass(slots=True)
class Visuals:
    """ Cooldowns, cast timers and other things happening over time. """
    # Cosmetics and Appearance
    color: tuple[int, int, int] = Colors.WHITE
    sprite_name: str = ""
    audio_name: str = ""



@dataclass(slots=True)
class GameObj:
    """ Players, NPCs, terrain, projectiles, hitboxes or similar. """
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell: int = Consts.EMPTY_ID

    # Status
    _loadout: Loadout = field(default_factory=Loadout)  # Spells and cooldowns
    _pos: Position = field(default_factory=Position)  # Coordinates and orientation in space
    _res: Resources = field(default_factory=Resources)  # HP, Mana, Ability Charges, etc.
    _state: Status = Status.EMPTY  # Alive, Dead, Despawned, Stunned, Casting, etc.
    current_target: int = Consts.EMPTY_ID
    selected_spell: int = Consts.EMPTY_ID

    # Combat stats
    is_attackable: bool = False
    gcd_mod: float = 1.0

    # Cosmetics and Appearance
    color: tuple[int, int, int] = Colors.WHITE
    sprite_name: str = ""
    audio_name: str = ""

    @classmethod
    def deserialize(cls, data: str) -> 'GameObj':
        d = json.loads(data) if isinstance(data, str) else data
        return cls(
            obj_id=d["oid"],
            parent_id=d["pid"],
            spawned_from_spell=d["sfs"],

            _loadout=Loadout.deserialize(d["l"]),
            _pos=Position.deserialize(d["p"]),
            _res=Resources.deserialize(d["r"]),

            _state=Status(d["st"]),
            current_target=d["tgt"],
            selected_spell=d["sel"],
            is_attackable=d["atk"],
            gcd_mod=d["gm"],

            color=(int(d["c"][0]), int(d["c"][1]), int(d["c"][2])),

            sprite_name=d["spr"],
            audio_name=d["aud"]
        )
    def serialize(self) -> str:
        return json.dumps({
            "oid": self.obj_id,
            "pid": self.parent_id,
            "sfs": self.spawned_from_spell,

            # Child object serialization: we use raw dict, not nested JSON strings
            "l": json.loads(self._loadout.serialize()),
            "p": json.loads(self._pos.serialize()),
            "r": json.loads(self._res.serialize()),

            "st": self._state.value,
            "tgt": self.current_target,
            "sel": self.selected_spell,
            "atk": self.is_attackable,
            "gm": self.gcd_mod,

            "c": list(self.color),

            "spr": self.sprite_name,
            "aud": self.audio_name
        })

    @classmethod
    def create_environment(cls, obj_id: int) -> 'GameObj':
        env_obj = GameObj()
        env_obj.obj_id=obj_id
        env_obj._state=Status.ENVIRONMENT
        env_obj._res.team=Faction.ALLIED
        env_obj.current_target=obj_id
        return env_obj

    @property
    def should_play_audio(self) -> bool:
        return self.audio_name is not None and self.audio_name != ""

    @property
    def should_render_sprite(self) -> bool:
        return self.sprite_name is not None and self.sprite_name != "" and self.is_visible

    @property
    def size(self) -> float:
        return 0.01 + math.sqrt(0.0001*abs(self._res.hp))

    @property
    def spell_modifier(self) -> float:
        return 1.0

    @property
    def is_environment(self) -> bool:
        return self._state in {Status.ENVIRONMENT}

    @property
    def is_visible(self) -> bool:
        return not self._state in {Status.ENVIRONMENT, Status.DESPAWNED}

    @property
    def is_despawned(self) -> bool:
        return self._state == Status.DESPAWNED

    @property
    def is_valid_source(self) -> bool:
        return self._state.is_valid_source

    @property
    def is_valid_target(self) -> bool:
        return self._state.is_valid_target

    @property
    def is_on_players_team(self) -> bool:
        return self._res.team.is_allied

    def get_gcd_progress(self, current_time: int) -> float:
        gcd = Consts.BASE_GCD * self.gcd_mod
        return min(1.0, (current_time - self._loadout.gcd_start) / gcd)

    # Newly added (below)
    def apply_damage(self, amount: float) -> None:
        self._res.hp -= amount

    def apply_healing(self, amount: float) -> None:
        self._res.hp += amount

    def set_gcd_start(self, timestamp: int) -> None:
        self._loadout.gcd_start = timestamp

    def despawn(self) -> None:
        self._state = Status.DESPAWNED

    def set_current_target(self, target_id: int) -> None:
        self.current_target = target_id

    def get_position_xy(self) -> tuple[float, float]:
        return (self._pos.x, self._pos.y)

    def set_position_xy(self, x: float, y: float) -> None:
        self._pos.x = Distance(x)
        self._pos.y = Distance(y)

    def is_within_range_of(self, other: 'GameObj', range_limit: float) -> bool:
        return self._pos.has_target_within_range(other._pos, range_limit)  # pylint: disable=protected-access

    def get_team(self) -> Faction:
        return self._res.team

    # New newly added:
    def move_towards_target(self, target: 'GameObj') -> None:
        self._pos.move_towards_destination(target._pos, self._pos.movement_speed)  # pylint: disable=protected-access

    def teleport_to_target(self, target: 'GameObj') -> None:
        self._pos.teleport_to_position(target._pos)  # pylint: disable=protected-access

    def move_up(self, multiplier: float) -> None:
        self._pos.move_up(multiplier)

    def move_left(self, multiplier: float) -> None:
        self._pos.move_left(multiplier)

    def move_down(self, multiplier: float) -> None:
        self._pos.move_down(multiplier)

    def move_right(self, multiplier: float) -> None:
        self._pos.move_right(multiplier)

    def get_movement_speed(self) -> float:
        return self._pos.movement_speed

    def get_spawn_timestamp(self) -> int:
        return self._loadout.spawn_timestamp

    def set_spawn_timestamp(self, timestamp: int) -> None:
        self._loadout.spawn_timestamp = timestamp

    def initialize_as_child(self, obj_id: int, parent: 'GameObj', spawn_timestamp: int, current_target: int) -> None:
        self.obj_id = obj_id
        self.parent_id = parent.obj_id
        self.set_spawn_timestamp(spawn_timestamp)
        self.current_target = current_target
        self._state = Status.ALIVE
        px, py = parent.get_position_xy()
        sx, sy = self.get_position_xy()
        self.set_position_xy(sx + px, sy + py)
        self._res.team = self._res.team if parent._state == Status.ENVIRONMENT else parent._res.team  # pylint: disable=protected-access

    # For GameObjFactory specifically
    def set_angle(self, angle: float) -> None:
        self._pos.angle = angle

    def set_movement_speed(self, speed: float) -> None:
        self._pos.movement_speed = speed

    def reset_resources(self, hp: float) -> None:
        self._res = Resources(hp=hp)

    def bind_spell(self, key_presses: KeyPresses, spell_id: int) -> None:
        self._loadout.bind_spell(key_presses, spell_id)

    def convert_controls_to_spell_ids(self, controls: Controls, obj_id: int) -> Iterable[int]:
        return self._loadout.convert_controls_to_spell_ids(controls, obj_id)

    # Team / Faction / Targeting logic


@dataclass(slots=True)
class ObjTemplate:
    """Positional data for GameObjs"""
    game_obj: GameObj = field(default_factory=GameObj)
    obj_controls: Optional[tuple[Controls, ...]] = None

    @property
    def get_position_xy(self) -> tuple[float, float]:
        return self.game_obj.get_position_xy()

    @property
    def get_movespeed(self) -> float:
        return self.game_obj.get_movement_speed()

    @classmethod
    def deserialize(cls, data: str) -> 'ObjTemplate':
        d = json.loads(data) if isinstance(data, str) else data
        controls = None
        if d["oc"] is not None:
            controls = tuple(Controls.deserialize(c) for c in d["oc"])
        return cls(
            game_obj=GameObj.deserialize(d["go"]),
            obj_controls=controls
        )
    def serialize(self) -> str:
        return json.dumps({
            "go": json.loads(self.game_obj.serialize()),
            "oc": (
                [json.loads(c.serialize()) for c in self.obj_controls]
                if self.obj_controls is not None else None
            )
        })

    def create_child(self, obj_id: int, parent: GameObj, spawn_timestamp: int, current_target: int) -> GameObj:
        child = self.create_obj_from_template()
        child.initialize_as_child(obj_id, parent, spawn_timestamp, current_target)
        return child

    def create_obj_from_template(self) -> GameObj:
        return CopyTools.full_copy(self.game_obj)