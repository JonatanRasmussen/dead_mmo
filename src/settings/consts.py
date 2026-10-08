

class Consts:
    EMPTY_ID_FOR_ID_GEN: int = 0
    EMPTY_EVENT_ID: int = 0
    EMPTY_OBJ_ID: int = 0
    EMPTY_SPELL_ID: int = 0
    EMPTY_INPUT_ID: int = 0
    EMPTY_ASSET_ID: int = 0
    TIMESTAMPS_PER_SECOND: int = 1000
    EMPTY_TIMESTAMP: int = -999_999
    EMPTY_ASSET_NAME: str = ""
    EMPTY_ERROR_CODE: str = ""

    EMPTY_SPELL_NAME: str = "empty_spell"
    INPUT_SPELL_NAME: str = "input_spell"

    IS_TARGETING_SELF = "is_targeting_self"
    IS_TARGETING_DESTINATION = "is_targeting_destination"
    IS_BOUND_TO_INPUT_ID = "is_bound_to_input_id"
    IS_SOURCE_DESTINATION_OF_TARGET = "is_destination_of_target"
    TRY_CAST_SELECTED_SPELL = "try_cast_selected_spell"

    MIN_ID: int = -999_999
    MAX_ID: int = 999_999

    EVENT_HEAP_MAX_ITERATIONS: int = 100_000

    BASE_GCD: int = 1000
    GLOBAL_MOVESPEED_TO_USE: float = 0.1
    MOVEMENT_UPDATES_PER_SECOND: int = 50

    FAILED_VALIDATION: str = "invalid"