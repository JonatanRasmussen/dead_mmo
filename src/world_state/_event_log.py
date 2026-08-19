import json
from typing import Iterable, ValuesView

from src.world_state._event_system import UpcomingEvent, Outcome
from src.settings import LogConfig
from src.utils import Logger


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
        self._event_log: dict[int, UpcomingEvent] = {}

    @property
    def view_all_events(self) -> ValuesView[UpcomingEvent]:
        return self._event_log.values()

    @property
    def get_successful_spell_ids(self) -> Iterable[int]:
        return (event.spell_id for event in self._event_log.values() if event.outcome_is_valid)

    def log_event(self, upcoming_event: UpcomingEvent, target_id: int, outcome: Outcome) -> None:
        finalized_event = upcoming_event.finalize_event(target_id, outcome)
        if self.DEBUG_PRINT_LOG_UDPATES:
            if finalized_event.outcome_is_valid or self.DEBUG_PRINT_UNSUCCESFUL_EVENTS:
                Logger.debug(finalized_event.event_summary, self.FILENAME_COMBAT_EVENT_LOG)
        assert finalized_event.event_id not in self._event_log, f"Event with ID {finalized_event.event_id} already exists in event_log."
        self._event_log[finalized_event.event_id] = finalized_event

    @staticmethod
    def summarize_new_aura_creation(new_aura_key: tuple[int, int, int]) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        Logger.debug(f"Aura {new_aura_key} WAS CREATED", EventLog.FILENAME_OBJ_UPDATES_LOG)

    @staticmethod
    def summarize_aura_deletion(aura_to_be_deleted_key: tuple[int, int, int]) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        Logger.debug(f"Aura {aura_to_be_deleted_key} WAS DELETED.", EventLog.FILENAME_OBJ_UPDATES_LOG)