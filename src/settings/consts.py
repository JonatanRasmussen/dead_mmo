

class Consts:
    EMPTY_ID: int = 0
    MIN_ID: int = -999_999
    MAX_ID: int = 999_999
    EMPTY_TIMESTAMP: int = -999

    EVENT_HEAP_MAX_ITERATIONS: int = 100_000

    BASE_GCD: int = 1000
    MOVEMENT_DISTANCE_PER_SECOND: float = 0.1
    MOVEMENT_UPDATES_PER_SECOND: int = 50

    @staticmethod
    def is_empty_id(id_num: int) -> bool:
        return id_num == Consts.EMPTY_ID

    @staticmethod
    def is_valid_id(id_num: int) -> bool:
        return not Consts.is_empty_id(id_num)