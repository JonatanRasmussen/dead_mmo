from typing import Iterable
from dataclasses import dataclass

from src.config import Consts
from .controls import Controls

@dataclass(slots=True)
class Loadout:
    """ Used by GameObjs to map controls inputs to spell events """

    # Ability movement slots
    start_move_up_id: int = Consts.EMPTY_ID
    stop_move_up_id: int = Consts.EMPTY_ID
    start_move_left_id: int = Consts.EMPTY_ID
    stop_move_left_id: int = Consts.EMPTY_ID
    start_move_down_id: int = Consts.EMPTY_ID
    stop_move_down_id: int = Consts.EMPTY_ID
    start_move_right_id: int = Consts.EMPTY_ID
    stop_move_right_id: int = Consts.EMPTY_ID

    # Ability spell slots
    next_target_id: int = Consts.EMPTY_ID
    ability_1_id: int = Consts.EMPTY_ID
    ability_2_id: int = Consts.EMPTY_ID
    ability_3_id: int = Consts.EMPTY_ID
    ability_4_id: int = Consts.EMPTY_ID

    def convert_controls_to_spell_ids(self, controls: Controls, obj_id: int) -> Iterable[int]:
        if controls.start_move_up:
            assert Consts.is_valid_id(self.start_move_up_id), f"Invalid spell ID for {obj_id}: start_move_up_id"
            yield self.start_move_up_id
        if controls.stop_move_up:
            assert Consts.is_valid_id(self.stop_move_up_id), f"Invalid spell ID for {obj_id}: stop_move_up_id"
            yield self.stop_move_up_id
        if controls.start_move_left:
            assert Consts.is_valid_id(self.start_move_left_id), f"Invalid spell ID for {obj_id}: start_move_left_id"
            yield self.start_move_left_id
        if controls.stop_move_left:
            assert Consts.is_valid_id(self.stop_move_left_id), f"Invalid spell ID for {obj_id}: stop_move_left_id"
            yield self.stop_move_left_id
        if controls.start_move_down:
            assert Consts.is_valid_id(self.start_move_down_id), f"Invalid spell ID for {obj_id}: start_move_down_id"
            yield self.start_move_down_id
        if controls.stop_move_down:
            assert Consts.is_valid_id(self.stop_move_down_id), f"Invalid spell ID for {obj_id}: stop_move_down_id"
            yield self.stop_move_down_id
        if controls.start_move_right:
            assert Consts.is_valid_id(self.start_move_right_id), f"Invalid spell ID for {obj_id}: start_move_right_id"
            yield self.start_move_right_id
        if controls.stop_move_right:
            assert Consts.is_valid_id(self.stop_move_right_id), f"Invalid spell ID for {obj_id}: stop_move_right_id"
            yield self.stop_move_right_id
        if controls.swap_target:
            assert Consts.is_valid_id(self.next_target_id), f"Invalid spell ID for {obj_id}: next_target_id"
            yield self.next_target_id
        if controls.ability_1:
            assert Consts.is_valid_id(self.ability_1_id), f"Invalid spell ID for {obj_id}: ability_1_id"
            yield self.ability_1_id
        if controls.ability_2:
            assert Consts.is_valid_id(self.ability_2_id), f"Invalid spell ID for {obj_id}: ability_2_id"
            yield self.ability_2_id
        if controls.ability_3:
            assert Consts.is_valid_id(self.ability_3_id), f"Invalid spell ID for {obj_id}: ability_3_id"
            yield self.ability_3_id
        if controls.ability_4:
            assert Consts.is_valid_id(self.ability_4_id), f"Invalid spell ID for {obj_id}: ability_4_id"
            yield self.ability_4_id
        assert not controls.is_empty, f"Controls for {obj_id} is empty."
