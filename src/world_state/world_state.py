from typing import Any, Iterable, ValuesView, Optional
from webbrowser import Galeon
import math

from src.settings import Consts
from src.world_state import Controls, KeyPresses
from src.world_state._controls_system import ControlsSystem
from src.world_state._game_obj_system import GameObj
from src.world_state import Behavior, DefaultIDs, Spell, Targeting
from src.world_state._event_system import UpcomingEvent, Outcome
from ._aura_handler import Aura, AuraHandler
from ._event_log import EventLog
from ._frame_heap import FrameHeap
from ._id_gen import IdGen
from ._spell_database import SpellDatabase
from ._combat_system import CombatSystem, ObjCombatData
from ._movement_system import MovementSystem, ObjMovementData



class WorldState:
    """ The entire game state of the save file that is currently in use """

    def __init__(self) -> None:
        self.spell_database: SpellDatabase = SpellDatabase()
        self._auras: AuraHandler = AuraHandler()
        self._event_heap: FrameHeap = FrameHeap()
        self._event_id_gen: IdGen = IdGen.create_preassigned_range(1, 100_000)
        self._event_log_for_each_frame: dict[int, EventLog] = {}
        #
        self._game_obj_id_gen: IdGen = IdGen.create_preassigned_range(1, 10_000)
        self._default_ids: DefaultIDs = DefaultIDs()
        #
        self._game_objs: dict[int, GameObj] = {}
        self._controls_system = ControlsSystem(self.spell_database)
        self._movement_system = MovementSystem(self.spell_database)
        self._combat_system = CombatSystem(self.spell_database)
        self._create_environment_obj()

    @property
    def view_game_objs(self) -> ValuesView[GameObj]:
        return self._game_objs.values()
    @property
    def default_ids(self) -> DefaultIDs:
        return self._default_ids
    @property
    def view_event_logs(self) -> dict[int, EventLog]:
        return self._event_log_for_each_frame

    def get_spell_ids_for_successful_events(self, timestamp: int) -> Iterable[int]:
        return (self._event_log_for_each_frame[timestamp].get_successful_spell_ids)

    def process_frame(self, player_inputs: list[str], frame_end: int) -> None:
        """Execute state updates for current frame"""
        for controls_event in self._create_events_from_controls(player_inputs, frame_end):
            self._event_heap.insert_event(controls_event)
        event_log = EventLog()
        while self._event_heap.has_unprocessed_events(frame_end):
            u_event = self._event_heap.pop_next_event()
            assert u_event.timestamp <= frame_end, f"frame ends at {frame_end}, but event has timestamp {u_event}."
            f_event = self._finalize_and_process_event(u_event)
            event_log.log_event(f_event)
        self._event_log_for_each_frame[frame_end] = event_log
        # debug sanity check
        for game_obj in self.view_game_objs:
            obj_id = game_obj.obj_id
            WorldState.debug_compare_ecs_to_gameobj(self._combat_system.game_obj_combat_dct[obj_id], self._movement_system.game_obj_positions_dct[obj_id], game_obj, frame_end)

    def process_setup_events(self, ingame_time: int, setup_spell_ids: list[int]) -> None:
        source_id = self.default_ids.environment_id
        for setup_event in self._create_setup_events(ingame_time, source_id, setup_spell_ids):
            self._event_heap.insert_event(setup_event)
        empty_list_of_player_inputs: list[str] = []
        self.process_frame(empty_list_of_player_inputs, ingame_time)

    def _finalize_and_process_event(self, u_event: UpcomingEvent) -> UpcomingEvent:
        source_obj = self.get_game_obj(u_event.source_id)
        spell = self.spell_database.get_spell(u_event.spell_id)
        target_obj = self._decide_targeting(u_event.target_id, u_event.is_aoe_targeting, source_obj, u_event.spell_id)
        expired_aura = u_event.is_aura_tick and not self._auras.aura_exists(u_event.aura_id)
        outcome = WorldState._decide_outcome(u_event.timestamp, source_obj, spell, target_obj, expired_aura, u_event.is_aoe_targeting)
        f_event = u_event.finalize_event(source_obj.obj_id, target_obj.obj_id, outcome)
        self._process_event(f_event, source_obj, spell, target_obj)
        return f_event


    def _process_event(self, f_event: UpcomingEvent, source_obj: GameObj, spell: Spell, target_obj: GameObj) -> None:
        timestamp = f_event.timestamp
        source_id = source_obj.obj_id
        target_id = target_obj.obj_id
        if f_event.outcome_is_valid:
            new_obj = self.handle_spawn(timestamp, source_obj, spell, target_id)
            if spell.has_aura_cancel:
                self._auras.remove_aura(source_id, spell.effect_id, target_id)
            new_aura_id = Consts.EMPTY_ID
            if spell.has_aura_apply:
                new_aura_id = self._auras.add_aura(timestamp, source_id, spell, target_id)
            if spell.has_cascading_events:
                for cascading_event in self._fetch_cascading_events(f_event, new_obj, source_obj, spell, target_obj, new_aura_id):
                    self._event_heap.insert_event(cascading_event)
            self._controls_system.apply_controls_event(timestamp, source_id, spell.spell_id)
            self._combat_system.apply_combat_event(timestamp, source_id, spell.spell_id, target_id)
            self._movement_system.apply_movement_event(timestamp, source_id, spell.spell_id, target_id)
            self.modify_game_obj(timestamp, source_obj, spell, target_obj)


    def _fetch_cascading_events(self, u_event: UpcomingEvent, new_obj: Optional[GameObj], source: GameObj, spell: Spell, target: GameObj, new_aura_id: int) -> Iterable[UpcomingEvent]:
        if new_obj is not None:
            scripted_spells = self._controls_system.get_scripted_spells(new_obj.obj_id, new_obj.get_spawn_timestamp())
            yield from self._create_control_events(new_obj.obj_id, new_obj.current_target, scripted_spells)
        if spell.is_area_of_effect and not u_event.is_aoe_targeting:
            target_ids = self._select_targets_for_aoe(source, target, self.view_game_objs)
            yield from self._create_aoe_events(u_event, target_ids)
        if spell.spell_sequence is not None:
            yield from self._create_spell_sequence_events(u_event, spell.spell_sequence)
        if spell.has_aura_apply:
            #aura = self._auras.get_aura_by_key(source.obj_id, spell.spell_id, target.obj_id)
            aura = self._auras.get_aura_by_id(new_aura_id)
            yield from self._create_aura_tick_events(aura)

    def _create_control_events(self, source_id: int, target_id: int, scripted_spells: Iterable[tuple[int, int, int]]) -> Iterable[UpcomingEvent]:
        for spell_id, timestamp, priority in scripted_spells:
            yield self._helper_for_create_event_from_control(source_id, target_id, timestamp, spell_id, priority)

    # The below methods are for upcoming_event creation
    def _create_aoe_events(self, u_event: UpcomingEvent, target_ids: Iterable[int]) -> Iterable[UpcomingEvent]:
        priority = u_event.priority
        for target_id in target_ids:
            priority += 1
            yield self._helper_for_create_aoe_events(u_event, target_id, priority)

    def _helper_for_create_aoe_events(self, u_event: UpcomingEvent, target_id: int, priority: int) -> UpcomingEvent:
        aoe_copy = u_event.create_copy()
        aoe_copy.event_id = self._event_id_gen.generate_new_id()
        aoe_copy.priority = priority
        aoe_copy.target_id = target_id
        aoe_copy.is_aoe_targeting = True
        return aoe_copy

    def _create_spell_sequence_events(self, u_event: UpcomingEvent, spell_sequence_ids: tuple[int, ...]) -> Iterable[UpcomingEvent]:
        priority = u_event.priority
        for next_spell_id in spell_sequence_ids:
            priority += 1
            yield self._helper_for_create_spell_sequence_events(u_event, next_spell_id, priority)

    def _helper_for_create_spell_sequence_events(self, u_event: UpcomingEvent, spell_sequence_id: int, priority: int) -> UpcomingEvent:
        seq_copy = u_event.create_copy()
        seq_copy.event_id = self._event_id_gen.generate_new_id()
        seq_copy.priority = priority
        seq_copy.spell_id = spell_sequence_id
        seq_copy.is_spell_sequence = True
        return seq_copy

    def _create_events_from_controls(self, player_inputs: list[str], timestamp: int) -> Iterable[UpcomingEvent]:
        player_id = self.default_ids.player_id
        input_event_order = 0
        if not player_inputs or player_id == Consts.EMPTY_ID:
            return
        player_obj = self.get_game_obj(player_id)
        spell_ids = self._controls_system.get_spell_ids_for_inputs(player_id, player_inputs, timestamp)
        for spell_id in spell_ids:
            input_event_order += 1
            assert spell_id != Consts.EMPTY_ID, f"Controls for {player_obj.obj_id} is casting empty spell ID, fix spell configs."
            yield self._helper_for_create_event_from_control(player_id, player_obj.current_target, timestamp, spell_id, input_event_order)


    def _helper_for_create_event_from_control(self, source_obj_id: int, source_current_target: int, controls_ingame_time: int, spell_id: int, priority: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=self._event_id_gen.generate_new_id(),
            timestamp=controls_ingame_time,
            source_id=source_obj_id,
            spell_id=spell_id,
            target_id=source_current_target,
            priority=priority,
        )

    def _create_aura_tick_events(self, aura: Aura) -> Iterable[UpcomingEvent]:
        priority = 0
        for tick_timestamp in aura.tick_timestamps:
            priority += 1
            yield self._helper_for_create_aura_tick_event(aura, tick_timestamp, priority)


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


    def _create_setup_events(self, timestamp: int, source_id: int, setup_spell_ids: list[int]) -> Iterable[UpcomingEvent]:
        for spell_id in setup_spell_ids:
            yield self._helper_for_create_setup_event(timestamp, source_id, spell_id)


    def _helper_for_create_setup_event(self, timestamp: int, source_id: int, spell_id: int) -> UpcomingEvent:
        return UpcomingEvent(
            event_id=self._event_id_gen.generate_new_id(),
            timestamp=timestamp,
            source_id=source_id,
            spell_id=spell_id
        )

    @staticmethod
    def _select_targets_for_aoe(source: GameObj, target: GameObj, all_game_objs: ValuesView[GameObj]) -> Iterable[int]:
        for obj in all_game_objs:
            team_is_hit_by_aoe = (obj.is_on_players_team == source.is_on_players_team) == (source.is_on_players_team == target.is_on_players_team)
            if team_is_hit_by_aoe and obj.is_valid_target and obj.obj_id != target.obj_id:
                yield obj.obj_id

    def _decide_targeting(self, aoe_target_id: int, is_aoe_targeting: bool, source_obj: GameObj, spell_id: int) -> GameObj:
        targeting = self._get_spell_targeting(spell_id)
        assert targeting not in {Targeting.NONE}, f"obj {source_obj.obj_id} is casting a spell with targeting=NONE"
        if targeting in {Targeting.SELF, Targeting.DEFAULT_FRIENDLY}:
            target_id = source_obj.obj_id
        elif targeting in {Targeting.TARGET, Targeting.TARGET_OF_TARGET} and Consts.is_valid_id(source_obj.current_target):
            target_id = source_obj.current_target
        elif targeting in {Targeting.PARENT, Targeting.TARGET_OF_PARENT} and Consts.is_valid_id(source_obj.parent_id):
            target_id = source_obj.parent_id
        elif targeting in {Targeting.DEFAULT_ENEMY}:
            if source_obj.is_on_players_team:
                target_id = self.default_ids.boss1_id
            else:
                target_id = self.default_ids.player_id
        elif targeting in {Targeting.TAB_TO_NEXT}:
            if not source_obj.is_on_players_team:
                target_id = self.default_ids.player_id
            elif source_obj.current_target == self.default_ids.boss1_id and self.default_ids.boss2_exists:
                target_id = self.default_ids.boss2_id
            elif Consts.is_valid_id(self.default_ids.boss1_id):
                target_id = self.default_ids.boss1_id
            else:
                # Not implemented. For now, let's assume boss1 always exist.
                target_id = self.default_ids.player_id
        else:
            target_id = self.default_ids.missing_target_id
        # If targeting the target of some external object, we must look it up
        if targeting in {targeting.TARGET_OF_TARGET, targeting.TARGET_OF_PARENT} and Consts.is_valid_id(target_id):
            obj_with_target_to_copy = self.get_game_obj(target_id)
            if Consts.is_valid_id(obj_with_target_to_copy.current_target):
                target_id = obj_with_target_to_copy.current_target
            else:
                target_id = self.default_ids.missing_target_id
        # If the following is true, ignore everything we just did (the target was already predetermined)
        if is_aoe_targeting:
            target_id = aoe_target_id
        # Finally return the GameObj associated with target_id
        if target_id == source_obj.obj_id:
            return source_obj
        return self.get_game_obj(target_id)


    @staticmethod
    def _decide_outcome(timestamp: int, source_obj: GameObj, spell: Spell, target_obj: GameObj, expired_aura: bool, is_aoe_targeting: bool) -> Outcome:
        # If triggered from aura, ensure aura is still active
        if expired_aura:
            return Outcome.AURA_NO_LONGER_EXISTS
        # Validate source
        if not is_aoe_targeting:  # This was previously validated if AoE
            if not source_obj.is_valid_source:
                return Outcome.SOURCE_IS_DISABLED
            if not WorldState._gcd_is_available(timestamp, source_obj, spell):
                return Outcome.GCD_NOT_READY
        # Validate target
        if not target_obj.is_valid_target and not source_obj.obj_id == target_obj.obj_id:
            return Outcome.TARGET_IS_INVALID
        # Validate source relative to target
        if not WorldState._is_within_range(source_obj, spell, target_obj):
            return Outcome.OUT_OF_RANGE
        # More outcome conditions to be added here.
        return Outcome.SUCCESS

    @staticmethod
    def _is_within_range(source_obj: GameObj, spell: Spell, target_obj: GameObj) -> bool:
        if not spell.has_range_limit:
            return True
        return source_obj.is_within_range_of(target_obj, spell.range_limit)

    @staticmethod
    def _gcd_is_available(timestamp: int, source_obj: GameObj, spell: Spell) -> bool:
        if not spell.flags & Behavior.TRIGGER_GCD:
            return True
        return source_obj.get_gcd_progress(timestamp) >= 1.0


    def _get_spell_targeting(self, spell_id: int) -> Targeting:
        spell = self.spell_database.get_spell(spell_id)
        return spell.targeting




    ######

    def has_game_obj(self, obj_id: int) -> bool:
        return obj_id in self._game_objs

    def get_game_obj(self, obj_id: int) -> GameObj:
        assert obj_id in self._game_objs, f"GameObj with ID {obj_id} does not exist."
        return self._game_objs.get(obj_id, GameObj())

    def add_game_obj(self, game_obj: GameObj) -> None:
        if EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            EventLog.summarize_new_obj_creation(game_obj)
        assert game_obj.obj_id not in self._game_objs, f"GameObj with ID {game_obj.obj_id} already exists."
        self._game_objs[game_obj.obj_id] = game_obj

    def update_game_obj(self, updated_game_obj: GameObj) -> None:
        if EventLog.DEBUG_PRINT_GAME_OBJ_UPDATES:
            pre_update_obj = self.get_game_obj(updated_game_obj.obj_id)
            EventLog.summarize_state_update(pre_update_obj, updated_game_obj)
        assert updated_game_obj.obj_id in self._game_objs, f"GameObj with ID {updated_game_obj.obj_id} does not exist."
        self._game_objs[updated_game_obj.obj_id] = updated_game_obj

    def handle_spawn(self, timestamp: int, source: GameObj, spell: Spell, target_id: int) -> Optional[GameObj]:
        template = spell.spawned_obj
        if template is None:
            return None
        new_obj_id = self._generate_new_game_obj_id()
        child = template.create_child(new_obj_id, source, timestamp, target_id)
        self.add_game_obj(child)

        parent_id = source.obj_id
        self._movement_system.spawn_game_obj(timestamp, parent_id, child.obj_id, spell.spell_id)
        self._combat_system.spawn_game_obj(timestamp, parent_id, child.obj_id, spell.spell_id, target_id)
        self._controls_system.spawn_game_obj(child.obj_id, spell.spell_id)
        self._update_default_ids(child, spell)
        return child

    @staticmethod
    def modify_game_obj(timestamp: int, source: GameObj, spell: Spell, target: GameObj) -> None:
        WorldState._apply_source_effects(spell, timestamp, source, target)
        WorldState._apply_target_effects(spell, source, target)

    @staticmethod
    def _apply_source_effects(spell: Spell, timestamp: int, source: GameObj, target: GameObj) -> None:
        flags = spell.flags
        if flags & Behavior.UPDATE_CURRENT_TARGET:
            source.set_current_target(target.obj_id)
        if flags & Behavior.TRIGGER_GCD:
            source.set_gcd_start(timestamp)
        if flags & Behavior.DESPAWN_SELF:
            source.despawn()
        if flags & Behavior.MOVE_TOWARDS_TARGET:
            source.move_towards_target(target)
        if flags & Behavior.TELEPORT_TO_TARGET:
            source.teleport_to_target(target)

    @staticmethod
    def _apply_target_effects(spell: Spell, source: GameObj, target: GameObj) -> None:
        flags = spell.flags
        if flags & (Behavior.STEP_UP | Behavior.STEP_LEFT | Behavior.STEP_DOWN | Behavior.STEP_RIGHT):
            speed = spell.power * target.get_movement_speed()
            if flags & Behavior.STEP_UP:
                target.move_up(speed)
            if flags & Behavior.STEP_LEFT:
                target.move_left(speed)
            if flags & Behavior.STEP_DOWN:
                target.move_down(speed)
            if flags & Behavior.STEP_RIGHT:
                target.move_right(speed)
        if flags & Behavior.DAMAGING:
            target.apply_damage(spell.power * source.spell_modifier)
        if flags & Behavior.HEALING:
            target.apply_healing(spell.power * source.spell_modifier)

    def _generate_new_game_obj_id(self) -> int:
        return self._game_obj_id_gen.generate_new_id()

    def _create_environment_obj(self) -> None:
        assert not self.default_ids.environment_exists, f"Environment is already initialized (ID={self._default_ids.environment_id})"
        obj_id: int = self._generate_new_game_obj_id()
        game_obj = GameObj.create_environment(obj_id)
        self.add_game_obj(game_obj)
        self._controls_system.create_environment_obj(obj_id)
        self._combat_system.create_environment_obj(obj_id)
        self._movement_system.create_environment_obj(obj_id)
        self.default_ids.environment_id = game_obj.obj_id

    def _update_default_ids(self, new_obj: GameObj, spell: Spell) -> None:
        if spell.flags & Behavior.SPAWN_BOSS:
            if not self._default_ids.boss1_exists:
                self._default_ids.boss1_id = new_obj.obj_id
            else:
                assert not self._default_ids.boss2_exists, "Second boss already exists."
                self._default_ids.boss2_id = new_obj.obj_id
        if spell.flags & Behavior.SPAWN_PLAYER:
            assert not self._default_ids.player_exists, "Player already exists."
            self._default_ids.player_id = new_obj.obj_id






    """
    def handle_spawn(self, timestamp: int, source: GameObj, spell: Spell, target_id: int) -> Optional[GameObj]:
        template = spell.spawned_obj
        if template is None:
            return None
        new_obj_id = self._game_obj_id_gen.generate_new_id()
        child = template.create_child(new_obj_id, source, timestamp, target_id)
        parent_id = source.obj_id
        self._movement_system.spawn_game_obj(timestamp, parent_id, child.obj_id, spell.spell_id)
        self._combat_system.spawn_game_obj(timestamp, parent_id, child.obj_id, spell.spell_id, target_id)
        self._update_default_ids(child, spell)
        return child

    def _update_default_ids(self, new_obj: GameObj, spell: Spell) -> None:
        if spell.flags & Behavior.SPAWN_BOSS:
            if not self._default_ids.boss1_exists:
                self._default_ids.boss1_id = new_obj.obj_id
            else:
                assert not self._default_ids.boss2_exists, "Second boss already exists."
                self._default_ids.boss2_id = new_obj.obj_id
        if spell.flags & Behavior.SPAWN_PLAYER:
            assert not self._default_ids.player_exists, "Player already exists."
            self._default_ids.player_id = new_obj.obj_id
    """

    @staticmethod
    def debug_compare_ecs_to_gameobj(
        combat_data: 'ObjCombatData',
        movement_data: 'ObjMovementData',
        external_obj: 'GameObj',
        current_time: Optional[int] = None
    ) -> bool:
        """
        Constructs a GameObj from ECS components and compares it to an external GameObj.
        Ignores small differences in dead-reckoned position caused by update timing.

        Handles independent X/Y timestamps from the new MovementSystem.
        """

        POSITION_ERROR_THRESHOLD = 0.012

        reconstructed = GameObj(obj_id=external_obj.obj_id)

        # Copy non-ECS fields
        reconstructed.spawned_from_spell = external_obj.spawned_from_spell
        reconstructed._loadout = external_obj._loadout
        reconstructed.selected_spell = external_obj.selected_spell
        reconstructed.is_attackable = external_obj.is_attackable
        reconstructed.color = external_obj.color
        reconstructed.sprite_name = external_obj.sprite_name
        reconstructed.audio_name = external_obj.audio_name

        reconstructed._pos.angle = external_obj._pos.angle
        reconstructed._pos.base_size = external_obj._pos.base_size
        reconstructed._res.team = external_obj._res.team

        # Combat data
        reconstructed.parent_id = combat_data.parent_id
        reconstructed._state = combat_data.status
        reconstructed.gcd_mod = combat_data.gcd_mod
        reconstructed.current_target = combat_data.current_target_id
        reconstructed._res.hp = combat_data.hp

        # Movement data
        # The old system's aura step for `current_time` has not been applied to
        # the GameObj yet at the point this hook runs, so read the ECS one tick
        # earlier to compare like with like. This is an observer artefact only —
        # it must NOT be baked into MovementSystem itself.
        OBSERVER_TICK_LAG_MS = MovementSystem.MS_PER_MOVEMENT_TICK if MovementSystem.CONSTRAIN_TO_TICK_RATE else 0
        if current_time is not None:#
            sample_time = max(
                movement_data.x_timestamp,
                movement_data.y_timestamp,
                current_time - OBSERVER_TICK_LAG_MS,
            )
            calc_x, calc_y = MovementSystem.extrapolate(movement_data, sample_time)
        else:
            calc_x = movement_data.x_pos
            calc_y = movement_data.y_pos

        DistanceType = type(external_obj._pos.x)
        reconstructed._pos.x = DistanceType(calc_x)
        reconstructed._pos.y = DistanceType(calc_y)
        reconstructed._pos.movement_speed = movement_data.movespeed

        # Compare base data
        base_matches = (
            reconstructed.gcd_mod == external_obj.gcd_mod and
            reconstructed.current_target == external_obj.current_target
        )

        resources_match = reconstructed._res == external_obj._res

        dx = float(reconstructed._pos.x) - float(external_obj._pos.x)
        dy = float(reconstructed._pos.y) - float(external_obj._pos.y)

        position_error = math.hypot(dx, dy)

        position_within_threshold = position_error <= POSITION_ERROR_THRESHOLD
        angle_matches = reconstructed._pos.angle == external_obj._pos.angle
        movespeed_matches = reconstructed._pos.movement_speed == external_obj._pos.movement_speed
        base_size_matches = reconstructed._pos.base_size == external_obj._pos.base_size

        position_matches = (
            position_within_threshold and
            angle_matches and
            movespeed_matches and
            base_size_matches
        )

        is_identical = base_matches and resources_match and position_matches

        # Single-line debug output
        if is_identical:
            pass
            #print(
            #    f"{current_time} [DEBUG] OK id={external_obj.obj_id} "
            #    f"pos=({float(reconstructed._pos.x):.3f},{float(reconstructed._pos.y):.3f})"
            #)
        else:
            issues = []

            if not base_matches:
                if reconstructed.gcd_mod != external_obj.gcd_mod:
                    issues.append(
                        f"gcd_mod mismatch: ECS={reconstructed.gcd_mod} != OBJ={external_obj.gcd_mod}"
                    )
                if reconstructed.current_target != external_obj.current_target:
                    issues.append(
                        f"current_target mismatch: ECS={reconstructed.current_target} != OBJ={external_obj.current_target}"
                    )

            if not resources_match:
                issues.append(
                    f"resources mismatch: ECS={reconstructed._res!r} != OBJ={external_obj._res!r}"
                )

            if not position_within_threshold:
                issues.append(
                    f"position exceeds threshold: delta=({dx:.4f},{dy:.4f}) "
                    f"err={position_error:.4f} > {POSITION_ERROR_THRESHOLD} "
                    f"(ECS=({float(reconstructed._pos.x):.3f},{float(reconstructed._pos.y):.3f}) "
                    f"OBJ=({float(external_obj._pos.x):.3f},{float(external_obj._pos.y):.3f}))"
                )
            if not angle_matches:
                issues.append(
                    f"angle mismatch: ECS={reconstructed._pos.angle} != OBJ={external_obj._pos.angle}"
                )
            if not movespeed_matches:
                issues.append(
                    f"movement_speed mismatch: ECS={reconstructed._pos.movement_speed} != OBJ={external_obj._pos.movement_speed}"
                )
            if not base_size_matches:
                issues.append(
                    f"base_size mismatch: ECS={reconstructed._pos.base_size} != OBJ={external_obj._pos.base_size}"
                )

            print(
                f"[{current_time} DEBUG] FAIL id={external_obj.obj_id} :: "
                f"{' | '.join(issues)}"
            )

        return is_identical