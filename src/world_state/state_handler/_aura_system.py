from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable
from src.settings import Consts, Optimizations


class AuraInvalidOutcomes(str, Enum):
    SOURCE_NOT_HOSTING_AURA = "source_not_hosting_aura"
    TARGET_NOT_HOSTING_AURA = "target_not_hosting_aura"
    SOURCE_NOT_OWNING_AURA_HOSTED_ON_TARGET = "does_source_have_aura_on_target"

class AuraValidation(str, Enum):
    IS_SOURCE_HOSTING_AURA = "is_source_hosting_aura"
    IS_TARGET_HOSTING_AURA = "is_target_hosting_aura"
    IS_SOURCE_OWNING_AURA_HOSTED_ON_TARGET = "does_source_have_aura_on_target"

class AuraEffect(str, Enum):
    APPLY_AURA_TO_SELF = "apply_aura_to_self"
    APPLY_AURA_TO_EVENT_TARGET = "apply_aura_to_event_target"


@dataclass(slots=True)
class ObjAuraData:
    obj_id: int = Consts.EMPTY_ID  # Both aura and non-aura game_objs share the same id_system
    parent_id: int = Consts.EMPTY_ID
    is_aura: bool = False  # Both aura and non-aura game_objs is spawned via the same pipeline
    owner_id: int = Consts.EMPTY_ID  # The first NON-AURA parent encountered in the chain of parenthood
    origin_id: int = Consts.EMPTY_ID  # The spell_id that spawned this aura obj
    host_id: int = Consts.EMPTY_ID  # The obj that this aura is acting on.


class AuraSystem:
    def __init__(self) -> None:
        self._data_dct: dict[int, ObjAuraData] = {}
        self._origin_dct: dict[int, list[ObjAuraData]] = {}

    def spawn_game_obj(self, new_obj_id: int, parent_id: int, spell_id: int) -> None:
        game_obj = ObjAuraData(obj_id=new_obj_id, parent_id=parent_id, origin_id=spell_id)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjAuraData(obj_id=obj_id)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjAuraData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjAuraData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self._data_dct.pop(obj_id)

    def get_target_ids_for_aoe(self, validation_value: float) -> Iterable[int]:
        origin_spell_id = round(validation_value)
        for matching_aura in self._find_auras_originating_from_spell(origin_spell_id):
            yield matching_aura.obj_id

    def validate_event(self, validation_type: str, validation_value: float, source_id: int, target_id: int) -> str:
        if validation_type == AuraValidation.IS_SOURCE_HOSTING_AURA:
            has_matching_aura = self._has_matching_aura(validation_value, source_id, None)
            if not has_matching_aura:
                return AuraInvalidOutcomes.SOURCE_NOT_HOSTING_AURA.value
        if validation_type == AuraValidation.IS_TARGET_HOSTING_AURA:
            has_matching_aura = self._has_matching_aura(validation_value, target_id, None)
            if not has_matching_aura:
                return AuraInvalidOutcomes.TARGET_NOT_HOSTING_AURA.value
        if validation_type == AuraValidation.IS_SOURCE_OWNING_AURA_HOSTED_ON_TARGET:
            has_matching_aura = self._has_matching_aura(validation_value, target_id, source_id)
            if not has_matching_aura:
                return AuraInvalidOutcomes.SOURCE_NOT_OWNING_AURA_HOSTED_ON_TARGET.value
        return ""

    def apply_effect(self, effect_type: str, source_id: int, target_id: int) -> None:
        if effect_type == AuraEffect.APPLY_AURA_TO_SELF:
            self._set_aura_host(source_id, source_id)
        elif effect_type == AuraEffect.APPLY_AURA_TO_EVENT_TARGET:
            self._set_aura_host(source_id, target_id)

    def _find_auras_originating_from_spell(self, spell_id: int) -> Iterable[ObjAuraData]:
        if Optimizations.ENABLE_FAST_AURA_LOOKUP:
            for data in self._origin_dct.get(spell_id, []):
                yield data
        else:
            for obj_id in self._data_dct:
                data = self.get_data(obj_id)
                if data.is_aura and data.origin_id == spell_id:
                    yield data

    def _set_aura_host(self, obj_id: int, host_id: int) -> None:
        obj_data = self.get_data(obj_id)
        assert not obj_data.is_aura, "Error: obj is already an aura."
        parent_data = self.get_data(obj_data.parent_id)
        obj_data.owner_id = parent_data.owner_id if parent_data.is_aura else parent_data.obj_id
        obj_data.is_aura = True
        obj_data.host_id = host_id
        if Optimizations.ENABLE_FAST_AURA_LOOKUP:
            self._origin_dct.setdefault(obj_data.origin_id, []).append(obj_data)

    def _has_matching_aura(self, validation_value: float, aura_host_id: int, aura_source_id: int | None) -> bool:
        origin_id = round(validation_value)
        auras = list(self._find_auras_originating_from_spell(origin_id))
        for aura in auras:
            if aura.origin_id == origin_id and aura.host_id == aura_host_id:
                if aura_source_id is None or aura.owner_id == aura_source_id:
                    return True
        return False