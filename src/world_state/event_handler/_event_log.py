from typing import Iterable, ValuesView

from src.settings import LogConfig
from src.utils import Logger
from ._combat_event import CombatEvent


class EventLog:
    FILENAME_COMBAT_EVENT_LOG = Logger.FILENAME_COMBAT_EVENT_LOG
    FILENAME_OBJ_UPDATES_LOG = Logger.FILENAME_OBJ_UPDATES_LOG

    DEBUG_PRINT_LOG_UDPATES = LogConfig.DEBUG_PRINT_LOG_UDPATES

    DEBUG_PRINT_UNSUCCESFUL_EVENTS = LogConfig.DEBUG_PRINT_UNSUCCESFUL_EVENTS
    DEBUG_PRINT_AURA_TICKS = LogConfig.DEBUG_PRINT_AURA_TICKS

    DEBUG_PRINT_AURA_UPDATES = LogConfig.DEBUG_PRINT_AURA_UPDATES
    DEBUG_PRINT_GAME_OBJ_UPDATES = LogConfig.DEBUG_PRINT_GAME_OBJ_UPDATES
    DEBUG_PRINT_GAME_OBJ_POSITIONAL_UPDATES = LogConfig.DEBUG_PRINT_GAME_OBJ_POSITIONAL_UPDATES

    def __init__(self) -> None:
        self._event_log: dict[int, CombatEvent] = {}

    @property
    def view_all_events(self) -> ValuesView[CombatEvent]:
        return self._event_log.values()

    @property
    def get_successful_spell_ids(self) -> Iterable[int]:
        return (event.spell_id for event in self._event_log.values() if event.outcome_is_valid)

    def log_event(self, finalized_event: CombatEvent) -> None:
        if self.DEBUG_PRINT_LOG_UDPATES:
            if finalized_event.outcome_is_valid or self.DEBUG_PRINT_UNSUCCESFUL_EVENTS:
                event_summary = f"[{finalized_event.timestamp:.3f}: id={finalized_event.event_id:04d}] {finalized_event.outcome} (obj_{finalized_event.source_id:04d} uses spell_{finalized_event.spell_id:04d} on obj_{finalized_event.target_id:04d}.)"
                Logger.debug(event_summary, self.FILENAME_COMBAT_EVENT_LOG)
        assert finalized_event.event_id not in self._event_log, f"Event with ID {finalized_event.event_id} already exists in event_log."
        self._event_log[finalized_event.event_id] = finalized_event