import json
import os

from src.world_state import KeyPresses, WorldState
from src.world_state._controls_data import InputTranslator

ALL_CHECKS = {"events_by_frame", "game_objs"}
#ALL_CHECKS = {"events_by_frame", "game_objs"}


class SimValidation:
    SNAPSHOT_DIR = "test_snapshots"

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def simulate_game_in_console(setup_spell_ids: list[int], scripted_player_input: dict[int, list[str]]) -> None:
        ingame_time = 0
        world_state = WorldState()
        world_state.process_setup_events(ingame_time, setup_spell_ids)

        SIMULATION_DURATION_MS = 10000
        UPDATES_PER_SECOND = 50
        FRAME_DURATION_MS = 1000 // UPDATES_PER_SECOND
        number_of_iterations = SIMULATION_DURATION_MS // FRAME_DURATION_MS

        player_inputs_this_frame: list[str] = []

        for _ in range(number_of_iterations):
            ingame_time += FRAME_DURATION_MS

            player_inputs_this_frame.clear()
            for timestamp, inputs in scripted_player_input.items():
                if (ingame_time - FRAME_DURATION_MS) < timestamp <= ingame_time:
                    for player_input in inputs:
                        player_inputs_this_frame.append(player_input)
            world_state.process_frame(player_inputs_this_frame, ingame_time)

        SimValidation._run_snapshot_test(world_state, snapshot_name=str(setup_spell_ids))

    @staticmethod
    def _run_snapshot_test(state: WorldState, snapshot_name: str = "default", checks: set[str] | None = None) -> None:
        if checks is None:
            checks = ALL_CHECKS

        skipped = ALL_CHECKS - checks
        if skipped:
            warning_lines = [
                "",
                "╔══════════════════════════════════════════════════════════════╗",
                "║                  ⚠  SNAPSHOT WARNING  ⚠                     ║",
                "║                                                              ║",
               f"║  The following checks are DISABLED for '{snapshot_name}':".ljust(63) + "║",
            ]
            for section in sorted(skipped):
                warning_lines.append(f"║    - {section}".ljust(63) + "║")
            warning_lines += [
                "║                                                              ║",
                "║  This snapshot test is NOT a full validation.                ║",
                "║  Re-enable all checks before merging.                        ║",
                "╚══════════════════════════════════════════════════════════════╝",
                "",
            ]
            print("\n".join(warning_lines))

        current_snapshot = SimValidation._capture_snapshot(state)
        snapshot_path = SimValidation._snapshot_path(snapshot_name)

        if not os.path.exists(snapshot_path):
            SimValidation._save_snapshot(current_snapshot, snapshot_path)
            print(f"[Snapshot] No existing snapshot found. Golden master saved to: {snapshot_path}")
            print("[Snapshot] Re-run the simulation to validate against it.")
            return

        golden_snapshot = SimValidation._load_snapshot(snapshot_path)
        diffs = SimValidation._diff_snapshots(golden_snapshot, current_snapshot, checks)

        if not diffs:
            print(f"[Snapshot] ✓ Simulation matches golden master '{snapshot_name}'. No differences found.")
            if skipped:
                print(f"[Snapshot] ⚠ Skipped checks: {sorted(skipped)}. This was NOT a full validation.")
        else:
            print(f"[Snapshot] ✗ Simulation DIFFERS from golden master '{snapshot_name}'.")
            print(f"[Snapshot] {len(diffs)} difference(s) found:\n")
            for diff in diffs:
                print(f"  {diff}")
            print(f"\n[Snapshot] If this change is intentional, delete '{snapshot_path}' and re-run to update the golden master.")
            raise AssertionError(f"Snapshot mismatch: {len(diffs)} difference(s). See output above.")

    # ------------------------------------------------------------------ #
    #  Capture                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _capture_snapshot(state: WorldState) -> dict:
        events_by_frame: dict[str, list[dict]] = {}
        for frame_time in sorted(state.view_event_logs.keys()):
            event_log = state.view_event_logs[frame_time]
            serialized_events = [
                json.loads(event.serialize())
                for event in sorted(event_log.view_all_events, key=lambda e: e.event_id)
            ]
            if serialized_events:
                events_by_frame[str(frame_time)] = serialized_events

        game_objs: dict[str, dict] = {
            str(obj.obj_id): json.loads(obj.serialize())
            for obj in sorted(state.view_game_objs, key=lambda o: o.obj_id)
        }

        return {
            "events_by_frame": events_by_frame,
            "game_objs": game_objs,
        }

    # ------------------------------------------------------------------ #
    #  Save / Load                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _snapshot_path(snapshot_name: str) -> str:
        os.makedirs(SimValidation.SNAPSHOT_DIR, exist_ok=True)
        return os.path.join(SimValidation.SNAPSHOT_DIR, f"{snapshot_name}.json")

    @staticmethod
    def _save_snapshot(snapshot: dict, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)

    @staticmethod
    def _load_snapshot(path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------ #
    #  Diff                                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _diff_snapshots(golden: dict, current: dict, checks: set[str]) -> list[str]:
        diffs: list[str] = []
        if "game_objs" in checks:
            SimValidation._diff_game_objs(golden.get("game_objs", {}), current.get("game_objs", {}), diffs)
        if "events_by_frame" in checks:
            SimValidation._diff_events(golden.get("events_by_frame", {}), current.get("events_by_frame", {}), diffs)
        return diffs

    @staticmethod
    def _diff_game_objs(golden_objs: dict, current_objs: dict, diffs: list[str]) -> None:
        all_ids = sorted(set(golden_objs.keys()) | set(current_objs.keys()), key=int)
        for obj_id in all_ids:
            if obj_id not in golden_objs:
                diffs.append(f"[GameObj {obj_id}] ADDED in current run")
                continue
            if obj_id not in current_objs:
                diffs.append(f"[GameObj {obj_id}] REMOVED in current run")
                continue
            SimValidation._diff_dict(
                golden_objs[obj_id],
                current_objs[obj_id],
                prefix=f"[GameObj {obj_id}]",
                diffs=diffs
            )

    @staticmethod
    def _diff_events(golden_frames: dict, current_frames: dict, diffs: list[str]) -> None:
        all_frames = sorted(set(golden_frames.keys()) | set(current_frames.keys()), key=int)
        for frame_time in all_frames:
            if frame_time not in golden_frames:
                count = len(current_frames[frame_time])
                diffs.append(f"[Frame {frame_time}] ADDED in current run ({count} event(s))")
                continue
            if frame_time not in current_frames:
                count = len(golden_frames[frame_time])
                diffs.append(f"[Frame {frame_time}] REMOVED in current run ({count} event(s))")
                continue

            golden_events = golden_frames[frame_time]
            current_events = current_frames[frame_time]

            if len(golden_events) != len(current_events):
                diffs.append(
                    f"[Frame {frame_time}] Event count changed: "
                    f"{len(golden_events)} (golden) → {len(current_events)} (current)"
                )

            for i, (g_evt, c_evt) in enumerate(zip(golden_events, current_events)):
                SimValidation._diff_dict(g_evt, c_evt, prefix=f"[Frame {frame_time}][Event {i}]", diffs=diffs)

    @staticmethod
    def _diff_dict(golden: dict, current: dict, prefix: str, diffs: list[str]) -> None:
        all_keys = set(golden.keys()) | set(current.keys())
        for key in sorted(all_keys):
            full_key = f"{prefix}.{key}"
            if key not in golden:
                diffs.append(f"{full_key}: ADDED → {current[key]!r}")
            elif key not in current:
                diffs.append(f"{full_key}: REMOVED (was {golden[key]!r})")
            elif isinstance(golden[key], dict) and isinstance(current[key], dict):
                SimValidation._diff_dict(golden[key], current[key], prefix=full_key, diffs=diffs)
            elif golden[key] != current[key]:
                diffs.append(f"{full_key}: {golden[key]!r} → {current[key]!r}")