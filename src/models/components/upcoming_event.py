from typing import Iterable
from dataclasses import dataclass

from src.config import Consts
from .aura import Aura
from .controls import Controls
from .game_obj import GameObj

@dataclass(slots=True)
class UpcomingEvent:
    timestamp: float = Consts.EMPTY_TIMESTAMP
    priority: int = 0

    source_id: int = Consts.EMPTY_ID
    spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID

    spell_modifier: float = 1.0

    aura_origin_spell_id: int = Consts.EMPTY_ID
    aura_start_time: float = Consts.EMPTY_TIMESTAMP
    is_spell_sequence: bool = False
    is_aoe_targeting: bool = False

    @property
    def key(self) -> tuple[float, int, int, int, int]:
        return (self.timestamp, self.priority, self.source_id, self.target_id, self.spell_id)

    @property
    def has_target(self) -> bool:
        return Consts.is_valid_id(self.target_id)

    @property
    def is_aura_tick(self) -> bool:
        return Consts.is_valid_id(self.aura_origin_spell_id)

    @staticmethod
    def create_aura_tick_events(aura: Aura, frame_start: float, frame_end: float) -> Iterable['UpcomingEvent']:
        """ Return an event for each tick happening this frame, excluding frame_start, including frame_end """
        priority = 0
        for tick_timestamp in aura.tick_timestamps:
            if frame_start < tick_timestamp <= frame_end:
                priority += 1
                yield UpcomingEvent(
                    timestamp=tick_timestamp,
                    source_id=aura.source_id,
                    spell_id=aura.periodic_spell_id,
                    target_id=aura.target_id,
                    priority=priority,
                    aura_origin_spell_id=aura.origin_spell_id,
                    aura_start_time=aura.start_time,
                )

    @staticmethod
    def create_events_from_controls(game_obj: GameObj, controls: Controls, frame_start: float, frame_end: float) -> Iterable['UpcomingEvent']:
        if not game_obj.is_despawned and frame_start < controls.ingame_time <= frame_end:
            input_event_order = 0
            for spell_id in game_obj.loadout.convert_controls_to_spell_ids(controls, game_obj.obj_id):
                input_event_order += 1
                assert spell_id != Consts.EMPTY_ID, f"Controls for {game_obj.obj_id} is casting empty spell ID, fix spell configs."
                yield UpcomingEvent(
                    timestamp=controls.ingame_time,
                    source_id=game_obj.obj_id,
                    spell_id=spell_id,
                    target_id=game_obj.current_target,
                    priority=input_event_order,
                )