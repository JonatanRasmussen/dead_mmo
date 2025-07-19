from typing import Iterable
from dataclasses import dataclass

from src.settings import Consts
from src.models.utils.copy_utils import CopyTools
from src.models.components import Controls, GameObj
from .aura import Aura


@dataclass(slots=True)
class UpcomingEvent:
    timestamp: int = Consts.EMPTY_TIMESTAMP
    priority: int = 0

    source_id: int = Consts.EMPTY_ID
    spell_id: int = Consts.EMPTY_ID
    target_id: int = Consts.EMPTY_ID

    spell_modifier: float = 1.0

    aura_origin_spell_id: int = Consts.EMPTY_ID
    aura_start_time: int = Consts.EMPTY_TIMESTAMP
    is_spell_sequence: bool = False
    is_aoe_targeting: bool = False

    @property
    def key(self) -> tuple[int, int, int, int, int]:
        return (self.timestamp, self.priority, self.source_id, self.target_id, self.spell_id)

    @property
    def has_target(self) -> bool:
        return Consts.is_valid_id(self.target_id)

    @property
    def is_aura_tick(self) -> bool:
        return Consts.is_valid_id(self.aura_origin_spell_id)

    def create_aoe_events(self, target_ids: Iterable[int]) -> Iterable['UpcomingEvent']:
        priority = self.priority
        for target_id in target_ids:
            priority += 1
            aoe_copy = self._create_copy()
            aoe_copy.priority = priority
            aoe_copy.target_id = target_id
            aoe_copy.is_aoe_targeting = True
            yield aoe_copy

    def create_spell_sequence_events(self, spell_sequence_ids: tuple[int, ...]) -> Iterable['UpcomingEvent']:
        priority = self.priority
        for next_spell_id in spell_sequence_ids:
            priority += 1
            seq_copy = self._create_copy()
            seq_copy.priority = priority
            seq_copy.spell_id = next_spell_id
            seq_copy.is_spell_sequence = True
            yield seq_copy

    @staticmethod
    def create_events_from_controls(source: GameObj, controls: Controls) -> Iterable['UpcomingEvent']:
        input_event_order = 0
        for spell_id in source.loadout.convert_controls_to_spell_ids(controls, source.obj_id):
            input_event_order += 1
            assert spell_id != Consts.EMPTY_ID, f"Controls for {source.obj_id} is casting empty spell ID, fix spell configs."
            yield UpcomingEvent(
                timestamp=controls.ingame_time,
                source_id=source.obj_id,
                spell_id=spell_id,
                target_id=source.current_target,
                priority=input_event_order,
            )

    @staticmethod
    def create_aura_tick_events(aura: Aura) -> Iterable['UpcomingEvent']:
        """ Return an event for each tick happening this frame, excluding frame_start, including frame_end """
        priority = 0
        for tick_timestamp in aura.tick_timestamps:
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
    def create_setup_events(timestamp: int, source_id: int, setup_spell_ids: list[int]) -> Iterable['UpcomingEvent']:
        for spell_id in setup_spell_ids:
            yield UpcomingEvent(timestamp=timestamp, source_id=source_id, spell_id=spell_id)

    def _create_copy(self) -> 'UpcomingEvent':
        return CopyTools.full_copy(self)
