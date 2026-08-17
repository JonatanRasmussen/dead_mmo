from src.settings import Consts
from src.world_state import Behavior, Targeting, Spell
from typing import Union, Mapping
from src.world_state import Controls, KeyPresses, Loadout
from src.world_state._game_obj_system import Distance, Faction, GameObj, ObjTemplate, Position, Resources


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
            _loadout=loadout,
            _pos=Position(x=Distance(0.0), y=Distance(0.05), movement_speed=speed, base_size=size),
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
            _loadout=loadout,
            _pos=Position(x=Distance(x), y=Distance(y)),
            _res=Resources(hp=hp),
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
            _loadout=loadout,
            _pos=Position(x=Distance(x), y=Distance(y)),
            _res=Resources(hp=hp),
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


class SpellFactory:
    def __init__(self, spell_id: int) -> None:
        self.spell: Spell = Spell(spell_id=spell_id)

    @property
    def spell_id(self) -> int:
        return self.spell.spell_id

    def build(self) -> Spell:
        return self.spell

    def add_flag(self, new_flag: Behavior) -> 'SpellFactory':
        assert not (self.spell.flags & new_flag), f"Flag {new_flag} is already set in {self.spell.flags}"
        self.spell.flags |= new_flag
        return self

    def _remove_flag(self, removed_flag: Behavior) -> 'SpellFactory':
        assert (self.spell.flags & removed_flag), f"Flag {removed_flag} is not currently set in {self.spell.flags}"
        self.spell.flags &= ~removed_flag
        return self

    def set_audio(self, audio_file_name: str) -> 'SpellFactory':
        assert (self.spell.audio_name == ""), f"Spell audio is already set to {self.spell.audio_name}."
        self.spell.audio_name = audio_file_name
        return self

    def use_gcd(self) -> 'SpellFactory':
        return self.add_flag(Behavior.TRIGGER_GCD)

    def aoe_cast(self) -> 'SpellFactory':
        return self.add_flag(Behavior.AOE)

    def despawn_self(self) -> 'SpellFactory':
        return self.add_flag(Behavior.DESPAWN_SELF)

    def teleport_to_parent(self) -> 'SpellFactory':
        return self.add_flag(Behavior.TELEPORT_TO_TARGET).set_targeting(Targeting.PARENT)

    def set_spell_sequence(self, sequence: tuple[int, ...]) -> 'SpellFactory':
        self.spell.spell_sequence = sequence
        return self

    def apply_aura(self, periodic_spell_id: int, duration: int, ticks: int) -> 'SpellFactory':
        self.spell.duration = duration
        self.spell.ticks = ticks
        self.spell.effect_id = periodic_spell_id
        return self.add_flag(Behavior.AURA_APPLY)

    def start_channel(self, periodic_spell_id: int, duration: int, ticks: int) -> 'SpellFactory':
        self.spell.duration = duration
        self.spell.ticks = ticks
        self.spell.effect_id = periodic_spell_id
        return self.add_flag(Behavior.START_CHANNEL)

    def cancel_aura(self, periodic_spell_id: int) -> 'SpellFactory':
        self.spell.effect_id = periodic_spell_id
        return self.add_flag(Behavior.AURA_CANCEL).add_flag(Behavior.STOP_CHANNEL)

    def stop_channel(self) -> 'SpellFactory':
        return self.add_flag(Behavior.STOP_CHANNEL)

    def inflict_damage(self, spell_power: float) -> 'SpellFactory':
        assert not (self.spell.flags & Behavior.HEALING), f"{self.spell.spell_id} with HEALING flag cannot be set to apply damage."
        assert not (self.spell.flags & Behavior.DAMAGING), f"{self.spell.spell_id} is already set to apply damage."
        self.spell.power = spell_power
        return self.add_flag(Behavior.DAMAGING)

    def restore_health(self, spell_power: float) -> 'SpellFactory':
        assert not (self.spell.flags & Behavior.DAMAGING), f"{self.spell.spell_id} with DAMAGING flag cannot be set to apply healing."
        assert not (self.spell.flags & Behavior.HEALING), f"{self.spell.spell_id} is already set to apply healing."
        self.spell.power = spell_power
        return self.add_flag(Behavior.HEALING)

    def set_range_limit(self, radius: float) -> 'SpellFactory':
        assert (self.spell.range_limit == Spell().range_limit), f"Range limit is already set to {self.spell.range_limit}."
        self.spell.range_limit = radius
        return self

    def cast_on_self(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.SELF)

    def cast_on_target(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.TARGET)

    def cast_on_target_of_target(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.TARGET_OF_TARGET)

    def cast_on_parent(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.PARENT)

    def cast_on_target_of_parent(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.TARGET_OF_PARENT)

    def cast_on_default_friendly(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.DEFAULT_FRIENDLY)

    def cast_on_default_enemy(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.DEFAULT_ENEMY)

    def cast_on_next_tab_target(self) -> 'SpellFactory':
        return self.set_targeting(Targeting.TAB_TO_NEXT)

    def update_current_target(self) -> 'SpellFactory':
        return self.add_flag(Behavior.UPDATE_CURRENT_TARGET)

    def spawn_minion(self, obj_template: ObjTemplate) -> 'SpellFactory':
        return self._spawn_obj(obj_template).cast_on_self()

    def spawn_projectile(self, obj_template: ObjTemplate) -> 'SpellFactory':
        return self._spawn_obj(obj_template).cast_on_target()

    def spawn_player(self, obj_template: ObjTemplate) -> 'SpellFactory':
        obj_template.game_obj._res.team = Faction.ALLIED
        return self._spawn_obj(obj_template).add_flag(Behavior.SPAWN_PLAYER).cast_on_self()

    def spawn_boss(self, obj_template: ObjTemplate) -> 'SpellFactory':
        obj_template.game_obj._res.team = Faction.ENEMY
        return self.add_flag(Behavior.SPAWN_BOSS).spawn_minion(obj_template)

    def _spawn_obj(self, obj_template: ObjTemplate) -> 'SpellFactory':
        obj_template.game_obj.spawned_from_spell=self.spell.spell_id
        self.spell.spawned_obj = obj_template
        return self.add_flag(Behavior.SPAWN_OBJ)

    def set_targeting(self, targeting: Targeting) -> 'SpellFactory':
        assert (self.spell.targeting == Targeting.NONE), f"Targeting is already set to {self.spell.targeting}."
        self.spell.targeting = targeting
        return self


class SpellTemplates:

    @staticmethod
    def directional_move_self(spell_id: int, direction: Behavior) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .add_flag(direction)
        )

    @staticmethod
    def apply_aura_to_self(spell_id: int, periodic_spell_id: int, duration: int, ticks: int) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .apply_aura(periodic_spell_id, duration, ticks)
        )

    @staticmethod
    def start_channel_on_self(spell_id: int, periodic_spell_id: int, duration: int, ticks: int) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .start_channel(periodic_spell_id, duration, ticks)
        )

    @staticmethod
    def cancel_channel_on_self(spell_id: int) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .stop_channel()
        )

    @staticmethod
    def start_move_self(spell_id: int, periodic_spell_id: int) -> SpellFactory:
        updates_per_second = Consts.MOVEMENT_UPDATES_PER_SECOND
        return SpellTemplates.start_channel_on_self(spell_id, periodic_spell_id, 60000, 60*updates_per_second)

    @staticmethod
    def cancel_aura_on_self(spell_id: int, aura_spell_id: int) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_self()
            .cancel_aura(aura_spell_id)
        )

    @staticmethod
    def damage_current_target(spell_id: int, power: float) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_target()
            .inflict_damage(power)
        )

    @staticmethod
    def damage_enemies_within_range(spell_id: int, power: float, radius: float) -> 'SpellFactory':
        return (
            SpellFactory(spell_id)
            .cast_on_default_enemy()
            .inflict_damage(power)
            .set_range_limit(radius)
        )

    @staticmethod
    def damage_current_target_when_within_range(spell_id: int, power: float, radius: float) -> 'SpellFactory':
        return (
            SpellFactory(spell_id)
            .cast_on_target()
            .inflict_damage(power)
            .set_range_limit(radius)
        )

    @staticmethod
    def heal_current_target(spell_id: int, power: float) -> SpellFactory:
        return (
            SpellFactory(spell_id)
            .cast_on_target()
            .restore_health(power)
        )

    @staticmethod
    def heal_allies_within_range(spell_id: int, power: float, radius: float) -> 'SpellFactory':
        return (
            SpellFactory(spell_id)
            .cast_on_default_friendly()
            .restore_health(power)
            .set_range_limit(radius)
        )

    @staticmethod
    def heal_current_target_when_within_range(spell_id: int, power: float, radius: float) -> 'SpellFactory':
        return (
            SpellFactory(spell_id)
            .cast_on_target()
            .restore_health(power)
            .set_range_limit(radius)
        )