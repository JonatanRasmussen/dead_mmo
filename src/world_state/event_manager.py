from typing import Any, Iterable, ValuesView, Optional

from src.settings import Consts
from src.models.components import Controls, KeyPresses, GameObj
from src.models.data import DefaultIDs, Spell, Targeting
from src.models.events import UpcomingEvent, Aura
from src.models.data import Behavior
from ._event_log import EventLog
from ._aura_handler import AuraHandler
from ._frame_heap import FrameHeap
from ._game_obj_handler import GameObjHandler
from ._id_gen import IdGen
from ._spell_database import SpellDatabase


class EventManager:
    EMPTY_EVENT_ID = 0

    def __init__(self) -> None:
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 100_000)
        self._event_log_for_each_frame: dict[int, EventLog] = {}
        self._current_event: UpcomingEvent = UpcomingEvent()

    @property
    def view_event_logs(self) -> dict[int, EventLog]:
        return self._event_log_for_each_frame

    @property
    def current_event_timestamp(self) -> int:
        return self._current_event.timestamp

    @property
    def current_event_source_id(self) -> int:
        return self._current_event.source_id

    @property
    def current_event_spell_id(self) -> int:
        return self._current_event.spell_id

    @property
    def current_event_target_id(self) -> int:
        return self._current_event.target_id


    def has_unprocessed_events(self, frame_end: int) -> bool:
        return self._event_heap.has_unprocessed_events(frame_end)

    def proceed_to_next_event(self) -> None:
        self._event_heap.pop_next_event()


    # def schedule_new_event(self) -> None:
    #    self._event_heap.insert_event(controls_event)

    def _helper_for_create_aoe_events(self, u_event: UpcomingEvent, target_id: int, priority: int) -> UpcomingEvent:
        aoe_copy = u_event.create_copy()
        aoe_copy.event_id = self._event_id_gen.generate_new_id()
        aoe_copy.priority = priority
        aoe_copy.target_id = target_id
        aoe_copy.is_aoe_targeting = True
        return aoe_copy

    def _helper_for_create_spell_sequence_events(self, u_event: UpcomingEvent, spell_sequence_id: int, priority: int) -> UpcomingEvent:
        seq_copy = u_event.create_copy()
        seq_copy.event_id = self._event_id_gen.generate_new_id()
        seq_copy.priority = priority
        seq_copy.spell_id = spell_sequence_id
        seq_copy.is_spell_sequence = True
        return seq_copy

    def _helper_for_create_event_from_control(self, source_obj_id: int, source_current_target: int, controls_ingame_time: int, spell_id: int, priority: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=self._event_id_gen.generate_new_id(),
            timestamp=controls_ingame_time,
            source_id=source_obj_id,
            spell_id=spell_id,
            target_id=source_current_target,
            priority=priority,
        )

    def _helper_for_create_aura_tick_event(self, aura: Aura, tick_timestamp: int, priority: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=self._event_id_gen.generate_new_id(),
            timestamp=tick_timestamp,
            source_id=aura.source_id,
            spell_id=aura.periodic_spell_id,
            target_id=aura.target_id,
            priority=priority,
            aura_id=aura.aura_id,
            aura_origin_spell_id=aura.origin_spell_id,
            aura_start_time=aura.start_time,
        )

    def _helper_for_create_setup_event(self, timestamp: int, source_id: int, spell_id: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=self._event_id_gen.generate_new_id(),
            timestamp=timestamp,
            source_id=source_id,
            spell_id=spell_id
        )