from typing import Dict

from src.models.event import UpcomingEvent, GameObj
from src.models.aura import Aura


class EventLog:
    DEBUG_PRINT_LOG_UDPATES = True
    DEBUG_PRINT_AURA_UPDATES = True
    DEBUG_PRINT_GAME_OBJ_UPDATES = True
    DEBUG_PRINT_GAME_OBJ_POSITIONAL_UPDATES = False

    def __init__(self) -> None:
        self._combat_event_log: Dict[int, UpcomingEvent] = {}

    def log_event(self, event: UpcomingEvent) -> None:
        if self.DEBUG_PRINT_LOG_UDPATES:
            print(event.event_summary)
        assert event.event_id not in self._combat_event_log, f"Event with ID {event.event_id} already exists."
        self._combat_event_log[event.event_id] = event

    @staticmethod
    def summarize_new_obj_creation(new_obj: GameObj) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        print(f"Obj {new_obj.obj_id:04d} WAS CREATED")

    @staticmethod
    def summarize_new_aura_creation(new_aura: Aura) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        print(f"Aura {new_aura.aura_id} WAS CREATED")

    @staticmethod
    def summarize_aura_deletion(aura_to_be_deleted: Aura) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return
        print(f"Aura {aura_to_be_deleted.aura_id} WAS DELETED.")

    @staticmethod
    def summarize_state_update(current: GameObj, updated: GameObj) -> None:
        if not EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            return

        # Helper function to format floats with 3 decimal places
        def fmt(value):
            if isinstance(value, float):
                return f"{value:.3f}"
            return value

        # Format object ID with 4 digits and leading zeros
        obj_id_fmt = f"{current.obj_id:04d}"

        # Appearance
        if current.color != updated.color:
            print(f"Obj {obj_id_fmt} COLOR update: {current.color} -> {updated.color}")

        # Status effects
        if current.status != updated.status:
            print(f"Obj {obj_id_fmt} STATUS update: {current.status} -> {updated.status}")

        # Targeting
        if current.is_allied != updated.is_allied:
            print(f"Obj {obj_id_fmt} ALLIANCE update: {current.is_allied} -> {updated.is_allied}")
        if current.current_target != updated.current_target:
            print(f"Obj {obj_id_fmt} TARGET update: {current.current_target:04d} -> {updated.current_target:04d}")
        if current.selected_spell != updated.selected_spell:
            print(f"Obj {obj_id_fmt} SELECTED SPELL update: {current.selected_spell} -> {updated.selected_spell}")

        # Combat stats
        if current.hp != updated.hp:
            print(f"Obj {obj_id_fmt} HP update: {fmt(current.hp)} -> {fmt(updated.hp)}")
        if current.movement_speed != updated.movement_speed:
            print(f"Obj {obj_id_fmt} SPEED update: {fmt(current.movement_speed)} -> {fmt(updated.movement_speed)}")
        if current.is_attackable != updated.is_attackable:
            print(f"Obj {obj_id_fmt} ATTACKABLE update: {current.is_attackable} -> {updated.is_attackable}")
        if current.is_player != updated.is_player:
            print(f"Obj {obj_id_fmt} PLAYER update: {current.is_player} -> {updated.is_player}")
        if current.gcd != updated.gcd:
            print(f"Obj {obj_id_fmt} GCD update: {fmt(current.gcd)} -> {fmt(updated.gcd)}")

        # Positional data
        if EventLog.DEBUG_PRINT_GAME_OBJ_POSITIONAL_UPDATES:
            if current.x != updated.x or current.y != updated.y or current.angle != updated.angle:
                print(f"Obj {obj_id_fmt} POSITION update: ({fmt(current.x)}, {fmt(current.y)}, {fmt(current.angle)}) -> ({fmt(updated.x)}, {fmt(updated.y)}, {fmt(updated.angle)}) (x, y, angle)")

        # Ability movement slots
        movement_slots = [
            ("MOVE UP START", current.start_move_up_id, updated.start_move_up_id),
            ("MOVE UP STOP", current.stop_move_up_id, updated.stop_move_up_id),
            ("MOVE LEFT START", current.start_move_left_id, updated.start_move_left_id),
            ("MOVE LEFT STOP", current.stop_move_left_id, updated.stop_move_left_id),
            ("MOVE DOWN START", current.start_move_down_id, updated.start_move_down_id),
            ("MOVE DOWN STOP", current.stop_move_down_id, updated.stop_move_down_id),
            ("MOVE RIGHT START", current.start_move_right_id, updated.start_move_right_id),
            ("MOVE RIGHT STOP", current.stop_move_right_id, updated.stop_move_right_id)
        ]

        for name, old_id, new_id in movement_slots:
            if old_id != new_id:
                print(f"Obj {obj_id_fmt} {name} update: {old_id:04d} -> {new_id:04d}")

        # Ability spell slots
        spell_slots = [
            ("NEXT TARGET", current.next_target_id, updated.next_target_id),
            ("ABILITY 1", current.ability_1_id, updated.ability_1_id),
            ("ABILITY 2", current.ability_2_id, updated.ability_2_id),
            ("ABILITY 3", current.ability_3_id, updated.ability_3_id),
            ("ABILITY 4", current.ability_4_id, updated.ability_4_id)
        ]

        for name, old_id, new_id in spell_slots:
            if old_id != new_id:
                print(f"Obj {obj_id_fmt} {name} update: {old_id:04d} -> {new_id:04d}")

        # Cooldown timestamps
        cooldown_timestamps = [
            ("SPAWN", current.spawn_timestamp, updated.spawn_timestamp),
            ("GCD START", current.gcd_start, updated.gcd_start),
            ("ABILITY 1 CD", current.ability_1_cd_start, updated.ability_1_cd_start),
            ("ABILITY 2 CD", current.ability_2_cd_start, updated.ability_2_cd_start),
            ("ABILITY 3 CD", current.ability_3_cd_start, updated.ability_3_cd_start),
            ("ABILITY 4 CD", current.ability_4_cd_start, updated.ability_4_cd_start)
        ]

        for name, old_timestamp, new_timestamp in cooldown_timestamps:
            if old_timestamp != new_timestamp:
                print(f"Obj {obj_id_fmt} {name} update: {fmt(old_timestamp)} -> {fmt(new_timestamp)}")