from enum import Enum, auto
from typing import Iterable, Optional, Protocol
from dataclasses import dataclass
from src.frontend_client.frontend_client import IRenderAction, IUiManager

class IUiUpdate(Protocol):
    source_id: int
    spell_id: int
    target_id: int
    is_new_spawn: bool
    is_aura_update: bool
    x_pos_delta: float
    x_velocity_delta: float
    y_pos_delta: float
    y_velocity_delta: float
    hp_curr_delta: float
    hp_max_delta: float
    mana_curr_delta: float
    mana_max_delta: float
    color_red_update: int
    color_green_update: int
    color_blue_update: int
    asset_id_update: int
    def is_obj_spawn(self) -> bool: ...
    def is_obj_despawn(self) -> bool: ...
    def is_hp_update(self) -> bool: ...
    def is_spell_heal(self) -> bool: ...

class UiEventType(Enum):
    EMPTY = auto()
    OBJ_SPAWN = auto()
    OBJ_DESPAWN = auto()
    DAMAGE = auto()
    HEAL = auto()

@dataclass(slots=True, frozen=True)
class UiEvent:
    event_type: UiEventType
    source_id: int
    spell_id: int
    target_id: int
    amount: float
    #more

    @classmethod
    def create_empty(cls) -> 'UiEvent':
        return cls(
            event_type = UiEventType.EMPTY,
            source_id = -1, #placeholder
            spell_id = -1, #placeholder
            target_id = -1, #placeholder
            amount = 0. #placeholder
        )

    @classmethod
    def create_from_serialized_event(cls, serialized_event: str) -> 'UiEvent':
        parts = serialized_event.split(",")
        if len(parts) < 5:
            raise ValueError(f"Serialized event has {len(parts)} parts, expected 5: {serialized_event!r}")
        event_type_str, source_id_str, spell_id_str, target_id_str, amount_str = parts[:5]
        try:
            event_type = UiEventType[event_type_str]
        except KeyError as exc:
            raise ValueError(f"Unknown UiEventType: {event_type_str!r}") from exc
        try:
            source_id = int(source_id_str)
            spell_id = int(spell_id_str)
            target_id = int(target_id_str)
            amount = float(amount_str)
        except ValueError as ex:
            raise ValueError(f"Invalid numeric value in serialized event: {serialized_event!r}") from ex
        return cls(event_type=event_type, source_id=source_id, spell_id=spell_id, target_id=target_id, amount=amount)


class IWeakAura(Protocol):
    def apply_event_to_weakaura(self, ui_event: UiEvent) -> None: ...
    # Not fully implemented

    def create_render_actions(self) -> Iterable[IRenderAction]: ...

class UiManager(IUiManager):
    def __init__(self) -> None:
        self._current_frame_id: int = 0
        self._weakauras: list[IWeakAura] = []
        self._render_actions: list[IRenderAction] = []

    def clear_current_frame_event_cache(self) -> None:
        self._current_frame_id += 1
        self._render_actions.clear()

    def apply_ui_update(self, serialized_event: str) -> None:
        pass
        #ui_event = UiEvent.create_from_serialized_event(serialized_event)
        #for weakaura in self._weakauras:
        #    weakaura.apply_event_to_weakaura(ui_event)

    def get_render_actions(self) -> Iterable[IRenderAction]:
        for weakaura in self._weakauras:
            yield from weakaura.create_render_actions()