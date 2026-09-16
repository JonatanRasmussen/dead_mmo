from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable
from src.settings import Consts

@dataclass(slots=True)
class ObjAuraData:
    obj_id: int = Consts.EMPTY_ID
    parent_id: int = Consts.EMPTY_ID
    spawned_from_spell_id: int = Consts.EMPTY_ID
    aura_source_id: int = Consts.EMPTY_ID
    aura_target_id: int = Consts.EMPTY_ID

class AuraEffect(str, Enum):
    TARGET_AURA_ONTO_PARENT = "aura_acting_on_parent"
    TARGET_AURA_ONTO_EVENT_TARGET = "aura_acting_on_event_target"

class AuraInvalidOutcomes(str, Enum):
    SOURCE_NOT_TARGETED_BY_AURA = "source_not_targeted_by_aura"
    TARGET_NOT_TARGETED_BY_AURA = "target_not_targeted_by_aura"
    SOURCE_NOT_TARGETED_BY_AURA_FROM_SOURCE = "source_not_targeted_by_aura_from_source"
    TARGET_NOT_TARGETED_BY_AURA_FROM_SOURCE = "target_not_targeted_by_aura_from_source"

class AuraValidation(str, Enum):
    IS_SOURCE_TARGETED_BY_AURA_WITH_SPELL_ID = "is_source_targeted_by_aura"
    IS_TARGET_TARGETED_BY_AURA_WITH_SPELL_ID = "is_target_targeted_by_aura"
    IS_SOURCE_TARGETED_BY_AURA_FROM_SOURCE_WITH_SPELL_ID = "is_source_targeted_by_aura_from_source"
    IS_TARGET_TARGETED_BY_AURA_FROM_SOURCE_WITH_SPELL_ID = "is_target_targeted_by_aura_from_source"

class AuraSystem:
    def __init__(self) -> None:
        self._data_dct: dict[int, ObjAuraData] = {}
        self._spawn_ids_dct: dict[int, list[ObjAuraData]] = {}

    def spawn_game_obj(self, new_obj_id: int, parent_id: int, spell_id: int) -> None:
        # GameObjs never spawn in as an aura
        game_obj = ObjAuraData(obj_id=new_obj_id, parent_id=parent_id, spawned_from_spell_id=spell_id)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjAuraData(obj_id=obj_id)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjAuraData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj
        self._spawn_ids_dct.setdefault(new_obj.spawned_from_spell_id, []).append(new_obj)

    def get_data(self, obj_id: int) -> ObjAuraData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        obj_data = self.get_data(obj_id)
        self._data_dct.pop(obj_id, None)

        # Remove obj from its spawned_from_spell_id list
        if obj_data.aura_target_id != Consts.EMPTY_ID:
            spawn_ids_lst = self._spawn_ids_dct.get(obj_data.spawned_from_spell_id)
            if spawn_ids_lst and obj_data in spawn_ids_lst:
                spawn_ids_lst.remove(obj_data)
                if not spawn_ids_lst:
                    del self._spawn_ids_dct[obj_data.spawned_from_spell_id]

        # Clean up this object's entry if it had any auras acting on it
        for spell_id, aura_list in list(self._spawn_ids_dct.items()):
            new_list = [aura for aura in aura_list if aura.aura_target_id != obj_id]
            if len(new_list) != len(aura_list):
                if not new_list:
                    del self._spawn_ids_dct[spell_id]
                else:
                    self._spawn_ids_dct[spell_id] = new_list

    def _set_aura_target(self, obj_id: int, aura_target_id: int) -> None:
        obj_data = self.get_data(obj_id)
        assert obj_data.aura_target_id == Consts.EMPTY_ID, "Error: Auras cannot have their target re-assigned."
        obj_data.aura_target_id = aura_target_id
        if aura_target_id != Consts.EMPTY_ID:
            self._spawn_ids_dct.setdefault(obj_data.spawned_from_spell_id, []).append(obj_data)

    def validate_event(self, validation_type: str, validation_value: float, source_id: int, target_id: int) -> str:
        if validation_type == AuraValidation.IS_SOURCE_TARGETED_BY_AURA_WITH_SPELL_ID:
            spell_id = round(validation_value)
            auras = self._spawn_ids_dct.get(spell_id, [])
            for aura in auras:
                if aura.aura_target_id == source_id:
                    return ""
            return AuraInvalidOutcomes.SOURCE_NOT_TARGETED_BY_AURA.value
        if validation_type == AuraValidation.IS_TARGET_TARGETED_BY_AURA_WITH_SPELL_ID:
            spell_id = round(validation_value)
            auras = self._spawn_ids_dct.get(spell_id, [])
            for aura in auras:
                if aura.aura_target_id == target_id:
                    return ""
            return AuraInvalidOutcomes.TARGET_NOT_TARGETED_BY_AURA.value
        if validation_type == AuraValidation.IS_SOURCE_TARGETED_BY_AURA_FROM_SOURCE_WITH_SPELL_ID:
            spell_id = round(validation_value)
            auras = self._spawn_ids_dct.get(spell_id, [])
            for aura in auras:
                if aura.aura_target_id == source_id and aura.aura_source_id == source_id:
                    return ""
            return AuraInvalidOutcomes.SOURCE_NOT_TARGETED_BY_AURA_FROM_SOURCE.value
        if validation_type == AuraValidation.IS_TARGET_TARGETED_BY_AURA_FROM_SOURCE_WITH_SPELL_ID:
            spell_id = round(validation_value)
            auras = self._spawn_ids_dct.get(spell_id, [])
            for aura in auras:
                if aura.aura_target_id == target_id and aura.aura_source_id == source_id:
                    return ""
            return AuraInvalidOutcomes.TARGET_NOT_TARGETED_BY_AURA_FROM_SOURCE.value
        return ""

    def apply_effect(self, effect_type: str, source_id: int, target_id: int) -> None:
        if effect_type == AuraEffect.TARGET_AURA_ONTO_PARENT:
            parent_id = self.get_data(source_id).parent_id
            self._set_aura_target(source_id, parent_id)
        elif effect_type == AuraEffect.TARGET_AURA_ONTO_EVENT_TARGET:
            self._set_aura_target(source_id, target_id)