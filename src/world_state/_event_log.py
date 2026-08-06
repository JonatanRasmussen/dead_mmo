import json
from typing import Iterable, ValuesView

from src.world_state._game_obj_system import GameObj
from src.world_state._event_system import UpcomingEvent
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

    def log_event(self, u_event: UpcomingEvent) -> None:
        if self.DEBUG_PRINT_LOG_UDPATES:
            if not u_event.is_aura_tick or self.DEBUG_PRINT_AURA_TICKS:
                if u_event.outcome_is_valid or self.DEBUG_PRINT_UNSUCCESFUL_EVENTS:
                    Logger.debug(u_event.event_summary, self.FILENAME_COMBAT_EVENT_LOG)
        assert u_event.event_id not in self._event_log, f"Event with ID {u_event.event_id} already exists in event_log."
        self._event_log[u_event.event_id] = u_event

    @staticmethod
    def summarize_new_obj_creation(new_obj: GameObj) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        Logger.debug(f"Obj {new_obj.obj_id:04d} WAS CREATED", EventLog.FILENAME_OBJ_UPDATES_LOG)

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

    @staticmethod
    def summarize_state_update(current: GameObj, updated: GameObj) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return

        def fmt(value):
            if isinstance(value, float):
                return f"{value:.3f}"
            if isinstance(value, int) and value > 1000:
                return f"{value / 1000.0:.3f}s"
            return str(value)

        def diff_dict(d1: dict, d2: dict, path: str = ""):
            """Recursively find differences between two dicts"""
            diffs = []

            keys = set(d1.keys()) | set(d2.keys())

            for key in keys:
                new_path = f"{path}.{key}" if path else key

                v1 = d1.get(key)
                v2 = d2.get(key)

                if isinstance(v1, dict) and isinstance(v2, dict):
                    diffs.extend(diff_dict(v1, v2, new_path))

                elif isinstance(v1, list) and isinstance(v2, list):
                    max_len = max(len(v1), len(v2))
                    for i in range(max_len):
                        item_path = f"{new_path}[{i}]"
                        try:
                            item1 = v1[i]
                        except IndexError:
                            item1 = None
                        try:
                            item2 = v2[i]
                        except IndexError:
                            item2 = None

                        if isinstance(item1, dict) and isinstance(item2, dict):
                            diffs.extend(diff_dict(item1, item2, item_path))
                        elif item1 != item2:
                            diffs.append((item_path, item1, item2))

                else:
                    if v1 != v2:
                        diffs.append((new_path, v1, v2))

            return diffs

        obj_id_fmt = f"{current.obj_id:04d}"

        # Serialize to dicts
        current_dict = json.loads(current.serialize())
        updated_dict = json.loads(updated.serialize())

        diffs = diff_dict(current_dict, updated_dict)

        for path, old, new in diffs:
            Logger.debug(
                f"Obj {obj_id_fmt} {path} update: {fmt(old)} -> {fmt(new)}",
                EventLog.FILENAME_OBJ_UPDATES_LOG
            )