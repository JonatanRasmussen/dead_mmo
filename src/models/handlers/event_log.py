from typing import Dict, ValuesView
from src.config import LogConfig
from src.models.components import Aura, FinalizedEvent, GameObj
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

    def __init__(self, frame_start: int, frame_end: int) -> None:
        self.frame_start: int = frame_start
        self.frame_end: int = frame_end
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
        if current.status != updated.status:
            Logger.debug(f"Obj {obj_id_fmt} STATUS update: {current.status} -> {updated.status}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Targeting
        if current.team.is_allied != updated.team.is_allied:
            Logger.debug(f"Obj {obj_id_fmt} ALLIANCE update: {current.team.is_allied} -> {updated.team.is_allied}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.current_target != updated.current_target:
            Logger.debug(f"Obj {obj_id_fmt} TARGET update: {current.current_target:04d} -> {updated.current_target:04d}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.selected_spell != updated.selected_spell:
            Logger.debug(f"Obj {obj_id_fmt} SELECTED SPELL update: {current.selected_spell} -> {updated.selected_spell}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Combat stats
        if current.res.hp != updated.res.hp:
            Logger.debug(f"Obj {obj_id_fmt} HP update: {fmt(current.res.hp)} -> {fmt(updated.res.hp)}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.mods.movement_speed != updated.mods.movement_speed:
            Logger.debug(f"Obj {obj_id_fmt} SPEED update: {fmt(current.mods.movement_speed)} -> {fmt(updated.mods.movement_speed)}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.is_attackable != updated.is_attackable:
            Logger.debug(f"Obj {obj_id_fmt} ATTACKABLE update: {current.is_attackable} -> {updated.is_attackable}", EventLog.FILENAME_OBJ_UPDATES_LOG)
        if current.gcd_mod != updated.gcd_mod:
            Logger.debug(f"Obj {obj_id_fmt} GCD update: {fmt(current.gcd_mod)} -> {fmt(updated.gcd_mod)}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Positional data
        if EventLog.DEBUG_PRINT_GAME_OBJ_POSITIONAL_UPDATES:
            if current.pos.x != updated.pos.x or current.pos.y != updated.pos.y or current.pos.angle != updated.pos.angle:
                Logger.debug(f"Obj {obj_id_fmt} POSITION update: ({fmt(current.pos.x)}, {fmt(current.pos.y)}, {fmt(current.pos.angle)}) -> ({fmt(updated.pos.x)}, {fmt(updated.pos.y)}, {fmt(updated.pos.angle)}) (x, y, angle)", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Ability movement slots
        movement_slots = [
            ("MOVE UP START", current.loadout.start_move_up_id, updated.loadout.start_move_up_id),
            ("MOVE UP STOP", current.loadout.stop_move_up_id, updated.loadout.stop_move_up_id),
            ("MOVE LEFT START", current.loadout.start_move_left_id, updated.loadout.start_move_left_id),
            ("MOVE LEFT STOP", current.loadout.stop_move_left_id, updated.loadout.stop_move_left_id),
            ("MOVE DOWN START", current.loadout.start_move_down_id, updated.loadout.start_move_down_id),
            ("MOVE DOWN STOP", current.loadout.stop_move_down_id, updated.loadout.stop_move_down_id),
            ("MOVE RIGHT START", current.loadout.start_move_right_id, updated.loadout.start_move_right_id),
            ("MOVE RIGHT STOP", current.loadout.stop_move_right_id, updated.loadout.stop_move_right_id)
        ]

        for name, old_id, new_id in movement_slots:
            if old_id != new_id:
                Logger.debug(f"Obj {obj_id_fmt} {name} update: {old_id:04d} -> {new_id:04d}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Ability spell slots
        spell_slots = [
            ("NEXT TARGET", current.loadout.next_target_id, updated.loadout.next_target_id),
            ("ABILITY 1", current.loadout.ability_1_id, updated.loadout.ability_1_id),
            ("ABILITY 2", current.loadout.ability_2_id, updated.loadout.ability_2_id),
            ("ABILITY 3", current.loadout.ability_3_id, updated.loadout.ability_3_id),
            ("ABILITY 4", current.loadout.ability_4_id, updated.loadout.ability_4_id)
        ]

        for name, old_id, new_id in spell_slots:
            if old_id != new_id:
                Logger.debug(f"Obj {obj_id_fmt} {name} update: {old_id:04d} -> {new_id:04d}", EventLog.FILENAME_OBJ_UPDATES_LOG)

        # Cooldown timestamps
        cooldown_timestamps = [
            ("SPAWN", current.cds.spawn_timestamp, updated.cds.spawn_timestamp),
            ("GCD START", current.cds.gcd_start, updated.cds.gcd_start),
            ("ABILITY 1 CD", current.cds.ability_1_cd_start, updated.cds.ability_1_cd_start),
            ("ABILITY 2 CD", current.cds.ability_2_cd_start, updated.cds.ability_2_cd_start),
            ("ABILITY 3 CD", current.cds.ability_3_cd_start, updated.cds.ability_3_cd_start),
            ("ABILITY 4 CD", current.cds.ability_4_cd_start, updated.cds.ability_4_cd_start)
        ]

        for name, old_timestamp, new_timestamp in cooldown_timestamps:
            if old_timestamp != new_timestamp:
                Logger.debug(f"Obj {obj_id_fmt} {name} update: {fmt(old_timestamp)} -> {fmt(new_timestamp)}", EventLog.FILENAME_OBJ_UPDATES_LOG)