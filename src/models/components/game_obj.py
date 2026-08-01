import json
import math
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Iterable


from src.settings import Colors, Consts
from .controls import Controls
from .faction import Faction
from .loadout import Loadout
from .status import Status
from .position import Position
from .resources import Resources
from .visuals import Visuals
from .distance import Distance
from .key_presses import KeyPresses

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
