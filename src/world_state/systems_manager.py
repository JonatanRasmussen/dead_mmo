from typing import Any, Iterable, Optional
from dataclasses import dataclass

from src.settings import Consts
from src.world_state import Controls, KeyPresses
from ._aura_handler import Aura, AuraHandler
from ._event_log import EventLog
from ._frame_heap import FrameHeap
from ._id_gen import IdGen
from ._spell_database import SpellDatabase
from ._event_system import EventSystem, UpcomingEvent, Outcome
from ._cooldown_system import CooldownSystem
from ._combat_system import CombatSystem
from ._movement_system import MovementSystem
from ._targeting_system import TargetingSystem
from ._vfx_and_sfx_system import VfxAndSfxSystem


@dataclass(slots=True)
class DisplayObj:
    obj_id: int
    pos_xy: tuple[float, float]
    size: float
    color_rgb: tuple[int, int, int]
    sprite_name: str


class SystemsManager:
    """ The entirely ECS-driven game state of the save file that is currently in use """

    def __init__(self) -> None:
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)

        self.spell_database: SpellDatabase = SpellDatabase()
        self._auras: AuraHandler = AuraHandler(self.spell_database)
        self._combat_system = CombatSystem(self.spell_database)
        self._cooldown_system = CooldownSystem(self.spell_database)
        self._event_system = EventSystem(self.spell_database)
        self._movement_system = MovementSystem(self.spell_database)
        self._targeting_system = TargetingSystem(self.spell_database)
        self._vfx_and_sfx_system = VfxAndSfxSystem(self.spell_database)

        self._create_environment_obj()

    @property
    def environment_id(self) -> int:
        return self._targeting_system.default_ids.environment_id
    @property
    def player_id(self) -> int:
        return self._targeting_system.default_ids.player_id

    @property
    def view_obj_ids(self) -> Iterable[int]:
        yield from self._event_system.game_obj_data_dct.keys()

    def get_display_obj(self, obj_id: int, timestamp: int) -> DisplayObj | None:
        if not self._combat_system.is_visible(obj_id):
            return None
        obj_vfx = self._vfx_and_sfx_system.get_obj_visuals(obj_id)
        if not obj_vfx:
            return None
        try:
            x, y = self._movement_system.get_position(obj_id, timestamp)
        except ValueError:
            # Object was likely despawned between ticks.
            return None
        return DisplayObj(
            obj_id=obj_id,
            pos_xy=(x, y),
            size=self._combat_system.get_size(obj_id),
            color_rgb=obj_vfx.color,
            sprite_name=obj_vfx.sprite_name,
        )

    def get_current_target_for_obj(self, obj_id: int) -> int:
        return self._targeting_system.get_current_target_for_obj(obj_id)

    def decide_event_target(self, source_id: int, spell_id: int, target_id: int, is_aoe_targeting: bool) -> int:
        return self._targeting_system.decide_targeting(source_id, spell_id, target_id, is_aoe_targeting)

    def select_targets_for_aoe(self, source_id: int, target_id: int) -> Iterable[int]:
        return self._targeting_system.select_targets_for_aoe(source_id, target_id)

    def decide_outcome(self, timestamp: int, source_id: int, spell_id: int, target_id: int, is_aoe_targeting: bool, expired_aura: bool) -> Outcome:
        if expired_aura:
            return Outcome.AURA_NO_LONGER_EXISTS
        if not is_aoe_targeting:
            if not self._targeting_system.is_valid_source(source_id):
                return Outcome.SOURCE_IS_DISABLED
            if not self._cooldown_system.is_gcd_ready(source_id, spell_id, timestamp):
                return Outcome.GCD_NOT_READY
        if not self._targeting_system.is_valid_target(target_id) and not source_id == target_id:
            return Outcome.TARGET_IS_INVALID
        if not self._movement_system.is_within_range(timestamp, source_id, spell_id, target_id):
            return Outcome.OUT_OF_RANGE
        return Outcome.SUCCESS

    def apply_event(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> None:
        self._cooldown_system.apply_cooldown_event(timestamp, source_id, spell_id)
        self._combat_system.apply_combat_event(timestamp, source_id, spell_id, target_id)
        self._movement_system.apply_movement_event(timestamp, source_id, spell_id, target_id)
        self._targeting_system.apply_targeting_event(timestamp, source_id, spell_id, target_id)

    def handle_aura(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        if self._event_system.has_aura_cancel(spell_id):
            effect_id = self._auras.get_effect_id(spell_id)
            self._auras.remove_aura(source_id, effect_id, target_id)
        new_aura_id = Consts.EMPTY_ID
        if self._event_system.has_aura_apply(spell_id):
            new_aura_id = self._auras.add_aura(timestamp, source_id, spell_id, target_id)
        return new_aura_id

    def handle_spawn(self, timestamp: int, source_id: int, spell_id: int, target_id: int) -> int:
        new_obj_id = Consts.EMPTY_ID
        if self._event_system.is_obj_spawn(spell_id):
            new_obj_id = self._game_obj_id_gen.generate_new_id()
            self._movement_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id)
            self._combat_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id, target_id)
            self._cooldown_system.spawn_game_obj(timestamp, new_obj_id, spell_id)
            self._event_system.spawn_game_obj(new_obj_id, spell_id)
            self._targeting_system.spawn_game_obj(timestamp, source_id, new_obj_id, spell_id, target_id)
            self._vfx_and_sfx_system.spawn_game_obj(new_obj_id, spell_id)
        return new_obj_id

    def _create_environment_obj(self) -> None:
        obj_id: int = self._game_obj_id_gen.generate_new_id()
        self._event_system.create_environment_obj(obj_id)
        self._combat_system.create_environment_obj(obj_id)
        self._movement_system.create_environment_obj(obj_id)
        self._targeting_system.create_environment_obj(obj_id)
        self._vfx_and_sfx_system.create_environment_obj(obj_id)
        self._targeting_system.default_ids.environment_id = obj_id