from dataclasses import dataclass
from enum import Enum
from typing import Iterable
from src.settings import Consts, Optimizations
from .system_interface import System


class AttachmentValidation(str, Enum):
    IS_SOURCE_HOSTING_ATTACHMENT = "is_source_hosting_attachment"
    IS_TARGET_HOSTING_ATTACHMENT = "is_target_hosting_attachment"
    IS_SOURCE_OWNING_ATTACHMENT_HOSTED_ON_TARGET = "does_source_have_attachment_on_target"


class AttachmentEffect(str, Enum):
    APPLY_ATTACHMENT_TO_PARENT = "apply_attachment_to_parent"
    APPLY_ATTACHMENT_TO_EVENT_TARGET = "apply_attachment_to_event_target"


@dataclass(slots=True)
class ObjAttachmentData:
    obj_id: int = Consts.EMPTY_ID  # Both attachment and non-attachment game_objs share the same id_system
    parent_id: int = Consts.EMPTY_ID
    is_attachment: bool = False  # Both attachment and non-attachment game_objs is spawned via the same pipeline
    owner_id: int = Consts.EMPTY_ID  # The first NON-ATTACHMENT parent encountered in the chain of parenthood
    origin_id: int = Consts.EMPTY_ID  # The spell_id that spawned this attachment obj
    host_id: int = Consts.EMPTY_ID  # The obj that this attachment is acting on.


class AttachmentSystem(System):

    def __init__(self) -> None:
        self._data_dct: dict[int, ObjAttachmentData] = {}
        self._origin_dct: dict[int, list[ObjAttachmentData]] = {}

    def spawn_game_obj(self, timestamp: int, new_obj_id: int, parent_id: int, spell_id: int, target_id: int) -> None:
        game_obj = ObjAttachmentData(obj_id=new_obj_id, parent_id=parent_id, origin_id=spell_id)
        self.add_data(new_obj_id, game_obj)

    def spawn_environment_obj(self, obj_id: int) -> None:
        environment_obj = ObjAttachmentData(obj_id=obj_id)
        self.add_data(obj_id, environment_obj)

    def add_data(self, new_obj_id: int, new_obj: ObjAttachmentData) -> None:
        assert new_obj_id not in self._data_dct, "Error: Obj already exists."
        self._data_dct[new_obj_id] = new_obj

    def get_data(self, obj_id: int) -> ObjAttachmentData:
        assert obj_id in self._data_dct, "Error: Obj does not exist."
        return self._data_dct[obj_id]

    def remove_data(self, obj_id: int) -> None:
        self._data_dct.pop(obj_id)

    def validate_event(self, validation_type: str, validation_value: float, timestamp: int, source_id: int, target_id: int) -> bool:
        if validation_type == AttachmentValidation.IS_SOURCE_HOSTING_ATTACHMENT:
            return self._has_matching_attachment(validation_value, source_id, None)
        if validation_type == AttachmentValidation.IS_TARGET_HOSTING_ATTACHMENT:
            return self._has_matching_attachment(validation_value, target_id, None)
        if validation_type == AttachmentValidation.IS_SOURCE_OWNING_ATTACHMENT_HOSTED_ON_TARGET:
            return self._has_matching_attachment(validation_value, target_id, source_id)
        return True

    def apply_effect(self, effect_type: str, effect_value: float, timestamp: int, source_id: int, target_id: int) -> None:
        if effect_type == AttachmentEffect.APPLY_ATTACHMENT_TO_PARENT:
            self._set_attachment_host(source_id, source_id)
        elif effect_type == AttachmentEffect.APPLY_ATTACHMENT_TO_EVENT_TARGET:
            self._set_attachment_host(source_id, target_id)

    def _find_attachments_originating_from_spell(self, spell_id: int) -> Iterable[ObjAttachmentData]:
        if Optimizations.ENABLE_FAST_ATTACHMENT_LOOKUP:
            for data in self._origin_dct.get(spell_id, []):
                yield data
        else:
            for obj_id in self._data_dct:
                data = self.get_data(obj_id)
                if data.is_attachment and data.origin_id == spell_id:
                    yield data

    def _set_attachment_host(self, obj_id: int, host_id: int) -> None:
        obj_data = self.get_data(obj_id)
        assert not obj_data.is_attachment, "Error: obj is already an attachment."
        parent_data = self.get_data(obj_data.parent_id)
        obj_data.owner_id = parent_data.owner_id if parent_data.is_attachment else parent_data.obj_id
        obj_data.is_attachment = True
        obj_data.host_id = host_id
        if Optimizations.ENABLE_FAST_ATTACHMENT_LOOKUP:
            self._origin_dct.setdefault(obj_data.origin_id, []).append(obj_data)

    def _has_matching_attachment(self, validation_value: float, attachment_host_id: int, attachment_source_id: int | None) -> bool:
        origin_id = round(validation_value)
        attachments = list(self._find_attachments_originating_from_spell(origin_id))
        for attachment in attachments:
            if attachment.origin_id == origin_id and attachment.host_id == attachment_host_id:
                if attachment_source_id is None or attachment.owner_id == attachment_source_id:
                    return True
        return False