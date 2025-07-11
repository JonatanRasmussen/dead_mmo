from typing import Union, Mapping

from src.config import Colors
from src.models.components import BaseStats, Controls, Distance, Faction, GameObj, KeyPresses, Loadout, ObjTemplate, Position, Resources, Status

class GameObjFactory:
    """Uses a builder pattern to create GameObj templates."""
    def __init__(self) -> None:
        self.obj_template: ObjTemplate = ObjTemplate()
        self.game_obj: GameObj = self.obj_template.game_obj

    def build(self) -> ObjTemplate:
        """Returns the configured GameObj template."""
        return self.obj_template

    def set_position(self, x: float, y: float, angle: float = 0.0) -> 'GameObjFactory':
        self.game_obj.pos = Position(x=Distance(x), y=Distance(y), angle=angle)
        return self

    def set_resources(self, hp: float) -> 'GameObjFactory':
        self.game_obj.res = Resources(hp=hp)
        return self

    def set_stats(self, movement_speed: float) -> 'GameObjFactory':
        self.game_obj.stats = BaseStats(movement_speed=movement_speed)
        return self

    def make_attackable(self, is_attackable: bool = True) -> 'GameObjFactory':
        self.game_obj.is_attackable = is_attackable
        return self

    def set_color(self, color: tuple[int, int, int]) -> 'GameObjFactory':
        self.game_obj.color = color
        return self

    def set_sprite(self, sprite_name: str) -> 'GameObjFactory':
        self.game_obj.sprite_name = sprite_name
        return self

    def bind_spell(self, key_presses: KeyPresses, spell_id: int) -> 'GameObjFactory':
        """Binds a spell to a key in the object's loadout."""
        self.game_obj.loadout.bind_spell(key_presses, spell_id)
        return self

class GameObjTemplates:
    @staticmethod
    def create_projectile(
            timeline: Mapping[int, Union[int, tuple[int, ...]]],
            speed: float,
            size: float,
            color: tuple[int, int, int]
        ) -> ObjTemplate:
        loadout, obj_controls = GameObjTemplates._create_loadout_from_scripted_timeline(timeline)
        game_obj = GameObj(
            loadout=loadout,
            pos=Position(x=Distance(0.0), y=Distance(0.05)),
            stats=BaseStats(movement_speed=speed, base_size=size),
            color=color,
        )
        return ObjTemplate(game_obj=game_obj, obj_controls=obj_controls)

    @staticmethod
    def create_enemy(
            timeline: Mapping[int, Union[int, tuple[int, ...]]],
            x: float,
            y: float,
            hp: float,
            color: tuple[int, int, int]
        ) -> ObjTemplate:
        loadout, obj_controls = GameObjTemplates._create_loadout_from_scripted_timeline(timeline)
        game_obj = GameObj(
            loadout=loadout,
            pos=Position(x=Distance(x), y=Distance(y)),
            res=Resources(hp=hp),
            color=color,
        )
        return ObjTemplate(game_obj=game_obj, obj_controls=obj_controls)

    @staticmethod
    def create_player(
            loadout: Loadout,
            x: float,
            y: float,
            hp: float,
            color: tuple[int, int, int],
            sprite_name: str,
        ) -> ObjTemplate:
        game_obj = GameObj(
            loadout=loadout,
            pos=Position(x=Distance(x), y=Distance(y)),
            res=Resources(hp=hp),
            color=color,
            sprite_name=sprite_name,
        )
        return ObjTemplate(game_obj=game_obj)


    @staticmethod
    def _create_loadout_from_scripted_timeline(
            scripted_timeline: Mapping[int, Union[int, tuple[int, ...]]]
        ) -> tuple['Loadout', tuple[Controls, ...]]:
        """Automatically generates a Loadout and Controls timeline from a {timestamp: (spell_id, ...)} dictionary."""
        available_keys = [key for key in KeyPresses if key != KeyPresses.NONE]
        all_spell_ids: list[int] = []
        for value in scripted_timeline.values():
            if isinstance(value, tuple):
                all_spell_ids.extend(value) # Add all spell_ids from the tuple.
            else:
                all_spell_ids.append(value) # Add the single spell_id.
        unique_spell_ids = sorted(list(set(all_spell_ids)))  # Ensure timeline is sorted such that key assignment is deterministic.
        if len(unique_spell_ids) > len(available_keys):
            raise ValueError(f"Timeline has {len(unique_spell_ids)} unique spell_ids but the limit is {len(available_keys)}.")
        spell_to_key_map: dict[int, KeyPresses] = dict(zip(unique_spell_ids, available_keys))  # Map each unique spell ID to an available key.
        loadout = Loadout()
        for spell_id, key_press in spell_to_key_map.items():  # Build the Loadout by binding the spells to their assigned keys.
            loadout.bind_spell(key_press, spell_id)
        controls_list = []
        for timestamp, value in scripted_timeline.items():  # Build the Controls timeline.
            spell_id_tuple = value if isinstance(value, tuple) else (value,)  # Normalize the value to always be a tuple.
            combined_keys = KeyPresses.NONE
            for spell_id in spell_id_tuple:  # For each spell at this timestamp, find its key and combine it.
                combined_keys |= spell_to_key_map[spell_id]
            if combined_keys != KeyPresses.NONE:
                controls_list.append(Controls(timeline_timestamp=timestamp, key_presses=combined_keys))
        controls_list.sort(key=lambda c: c.timeline_timestamp)  # Sort the controls by timestamp to ensure they are in chronological order.
        return loadout, tuple(controls_list)