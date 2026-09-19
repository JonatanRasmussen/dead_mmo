from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable
from src.settings import Consts, Optimizations


class AttatchmentInvalidOutcomes(str, Enum):
    SOURCE_NOT_HOSTING_ATTATCHMENT = "source_not_hosting_attatchment"
    TARGET_NOT_HOSTING_ATTATCHMENT = "target_not_hosting_attatchment"
    SOURCE_NOT_OWNING_ATTATCHMENT_HOSTED_ON_TARGET = "does_source_have_attatchment_on_target"

class AttatchmentValidation(str, Enum):
    IS_SOURCE_HOSTING_ATTATCHMENT = "is_source_hosting_attatchment"
    IS_TARGET_HOSTING_ATTATCHMENT = "is_target_hosting_attatchment"
    IS_SOURCE_OWNING_ATTATCHMENT_HOSTED_ON_TARGET = "does_source_have_attatchment_on_target"

class AttatchmentEffect(str, Enum):
    APPLY_ATTATCHMENT_TO_PARENT = "apply_attatchment_to_parent"
    APPLY_ATTATCHMENT_TO_EVENT_TARGET = "apply_attatchment_to_event_target"

@dataclass(slots=True)
class ObjAttatchmentData:
    obj_id: int = Consts.EMPTY_ID  # Both attatchment and non-attatchment game_objs share the same id_system
    parent_id: int = Consts.EMPTY_ID
    is_attatchment: bool = False  # Both attatchment and non-attatchment game_objs is spawned via the same pipeline
    owner_id: int = Consts.EMPTY_ID  # The first NON-ATTATCHMENT parent encountered in the chain of parenthood
    origin_id: int = Consts.EMPTY_ID  # The spell_id that spawned this attatchment obj
    host_id: int = Consts.EMPTY_ID  # The obj that this attatchment is acting on.


class AttatchmentSystem:
    def __init__(self) -> None:
        self._data_dct: dict[int, ObjAttatchmentData] = {}
        self._origin_dct: dict[int, list[ObjAttatchmentData]] = {}

    def spawn_game_obj(self, new_obj_id: int, parent_id: int, spell_id: int) -> None:
        game_obj = ObjAttatchmentData(obj_id=new_obj_id, parent_id=parent_id, origin_id=spell_id)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjAttatchmentData(obj_id=obj_id)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjAttatchmentData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjAttatchmentData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self._data_dct.pop(obj_id)

    def validate_event(self, validation_type: str, validation_value: float, source_id: int, target_id: int) -> str:
        if validation_type == AttatchmentValidation.IS_SOURCE_HOSTING_ATTATCHMENT:
            has_matching_attatchment = self._has_matching_attatchment(validation_value, source_id, None)
            if not has_matching_attatchment:
                return AttatchmentInvalidOutcomes.SOURCE_NOT_HOSTING_ATTATCHMENT.value
        if validation_type == AttatchmentValidation.IS_TARGET_HOSTING_ATTATCHMENT:
            has_matching_attatchment = self._has_matching_attatchment(validation_value, target_id, None)
            if not has_matching_attatchment:
                return AttatchmentInvalidOutcomes.TARGET_NOT_HOSTING_ATTATCHMENT.value
        if validation_type == AttatchmentValidation.IS_SOURCE_OWNING_ATTATCHMENT_HOSTED_ON_TARGET:
            has_matching_attatchment = self._has_matching_attatchment(validation_value, target_id, source_id)
            if not has_matching_attatchment:
                return AttatchmentInvalidOutcomes.SOURCE_NOT_OWNING_ATTATCHMENT_HOSTED_ON_TARGET.value
        return ""

    def apply_effect(self, effect_type: str, source_id: int, target_id: int) -> None:
        if effect_type == AttatchmentEffect.APPLY_ATTATCHMENT_TO_PARENT:
            self._set_attatchment_host(source_id, source_id)
        elif effect_type == AttatchmentEffect.APPLY_ATTATCHMENT_TO_EVENT_TARGET:
            self._set_attatchment_host(source_id, target_id)

    def _find_attatchments_originating_from_spell(self, spell_id: int) -> Iterable[ObjAttatchmentData]:
        if Optimizations.ENABLE_FAST_ATTATCHMENT_LOOKUP:
            for data in self._origin_dct.get(spell_id, []):
                yield data
        else:
            for obj_id in self._data_dct:
                data = self.get_data(obj_id)
                if data.is_attatchment and data.origin_id == spell_id:
                    yield data

    def _set_attatchment_host(self, obj_id: int, host_id: int) -> None:
        obj_data = self.get_data(obj_id)
        assert not obj_data.is_attatchment, "Error: obj is already an attatchment."
        parent_data = self.get_data(obj_data.parent_id)
        obj_data.owner_id = parent_data.owner_id if parent_data.is_attatchment else parent_data.obj_id
        obj_data.is_attatchment = True
        obj_data.host_id = host_id
        if Optimizations.ENABLE_FAST_ATTATCHMENT_LOOKUP:
            self._origin_dct.setdefault(obj_data.origin_id, []).append(obj_data)

    def _has_matching_attatchment(self, validation_value: float, attatchment_host_id: int, attatchment_source_id: int | None) -> bool:
        origin_id = round(validation_value)
        attatchments = list(self._find_attatchments_originating_from_spell(origin_id))
        for attatchment in attatchments:
            if attatchment.origin_id == origin_id and attatchment.host_id == attatchment_host_id:
                if attatchment_source_id is None or attatchment.owner_id == attatchment_source_id:
                    return True
        return False