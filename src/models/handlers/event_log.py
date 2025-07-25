from typing import ValuesView

from src.models.components import GameObj
from src.settings import LogConfig
from src.models.events import Aura, FinalizedEvent
from src.models.utils import Logger


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
        self._combat_event_log: dict[int, FinalizedEvent] = {}

    @property
    def view_all_events(self) -> ValuesView[FinalizedEvent]:
        return self._combat_event_log.values()

    def log_event(self, event: FinalizedEvent) -> None:
        if self.DEBUG_PRINT_LOG_UDPATES:
            if not event.upcoming_event.is_aura_tick or self.DEBUG_PRINT_AURA_TICKS:
                if event.outcome_is_valid or self.DEBUG_PRINT_UNSUCCESFUL_EVENTS:
                    Logger.debug(event.event_summary, self.FILENAME_COMBAT_EVENT_LOG)
        assert event.event_id not in self._combat_event_log, f"Event with ID {event.event_id} already exists in event_log."
        self._combat_event_log[event.event_id] = event

    @staticmethod
    def summarize_new_obj_creation(new_obj: GameObj) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        Logger.debug(f"Obj {new_obj.obj_id:04d} WAS CREATED", EventLog.FILENAME_OBJ_UPDATES_LOG)

    @staticmethod
    def summarize_new_aura_creation(new_aura: Aura) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        Logger.debug(f"Aura {new_aura.key} WAS CREATED", EventLog.FILENAME_OBJ_UPDATES_LOG)

    @staticmethod
    def summarize_aura_deletion(aura_to_be_deleted: Aura) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        Logger.debug(f"Aura {aura_to_be_deleted.key} WAS DELETED.", EventLog.FILENAME_OBJ_UPDATES_LOG)

    @staticmethod
    def summarize_state_update(current: GameObj, updated: GameObj) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return

        def fmt(value):
            """ Helper function to format floats with 3 decimal places """
            if isinstance(value, float):
                return f"{value:.3f}"
            if isinstance(value, int) and value > 1000: # Heuristic to guess if it's a timestamp
                return f"{value / 1000.0:.3f}s"
            return str(value) # Convert all to string for consistency

        # Format object ID with 4 digits and leading zeros
        obj_id_fmt = f"{current.obj_id:04d}"

        # Appearance
        if current.color != updated.color:
            Logger.debug(f"Obj {obj_id_fmt} COLOR update: {current.color} -> {updated.color}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Status effects
        if current.state != updated.state:
            Logger.debug(f"Obj {obj_id_fmt} STATUS update: {current.state} -> {updated.state}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Targeting
        if current.res.team.is_allied != updated.res.team.is_allied:
            Logger.debug(f"Obj {obj_id_fmt} ALLIANCE update: {current.res.team.is_allied} -> {updated.res.team.is_allied}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.current_target != updated.current_target:
            Logger.debug(f"Obj {obj_id_fmt} TARGET update: {current.current_target:04d} -> {updated.current_target:04d}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.selected_spell != updated.selected_spell:
            Logger.debug(f"Obj {obj_id_fmt} SELECTED SPELL update: {current.selected_spell} -> {updated.selected_spell}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Combat stats
        if current.res.hp != updated.res.hp:
            Logger.debug(f"Obj {obj_id_fmt} HP update: {fmt(current.res.hp)} -> {fmt(updated.res.hp)}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.pos.movement_speed != updated.pos.movement_speed:
            Logger.debug(f"Obj {obj_id_fmt} SPEED update: {fmt(current.pos.movement_speed)} -> {fmt(updated.pos.movement_speed)}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.is_attackable != updated.is_attackable:
            Logger.debug(f"Obj {obj_id_fmt} ATTACKABLE update: {current.is_attackable} -> {updated.is_attackable}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.gcd_mod != updated.gcd_mod:
            Logger.debug(f"Obj {obj_id_fmt} GCD update: {fmt(current.gcd_mod)} -> {fmt(updated.gcd_mod)}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Positional data
        if EventLog.DEBUG_PRINT_GAME_OBJ_POSITIONAL_UPDATES:
            if current.pos.x != updated.pos.x or current.pos.y != updated.pos.y or current.pos.angle != updated.pos.angle:
                Logger.debug(f"Obj {obj_id_fmt} POSITION update: ({fmt(current.pos.x)}, {fmt(current.pos.y)}, {fmt(current.pos.angle)}) -> ({fmt(updated.pos.x)}, {fmt(updated.pos.y)}, {fmt(updated.pos.angle)}) (x, y, angle)", EventLog.FILENAME_OBJ_UPDATES_LOG)

        for i in range (len(current.loadout.spell_ids)):
            if current.loadout.spell_ids[i] != updated.loadout.spell_ids[i]:
                old_id = current.loadout.spell_ids[i]
                new_id = updated.loadout.spell_ids[i]
                Logger.debug(f"Obj {obj_id_fmt} loadout update at index {i}: {old_id:04d} -> {new_id:04d}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Cooldown timestamps
        cooldown_timestamps = [
            ("SPAWN", current.loadout.spawn_timestamp, updated.loadout.spawn_timestamp),
            ("GCD START", current.loadout.gcd_start, updated.loadout.gcd_start)
        ]

        for name, old_timestamp, new_timestamp in cooldown_timestamps:
            if old_timestamp != new_timestamp:
                Logger.debug(f"Obj {obj_id_fmt} {name} update: {fmt(old_timestamp)} -> {fmt(new_timestamp)}", EventLog.FILENAME_OBJ_UPDATES_LOG)