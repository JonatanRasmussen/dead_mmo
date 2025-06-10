

class Consts:
    EMPTY_ID: int = 0
    MIN_ID: int = -999_999
    MAX_ID: int = 999_999
    EMPTY_TIMESTAMP: float = -999.9

    @staticmethod
    def is_empty_id(id_num: int) -> bool:
        return id_num == Consts.EMPTY_ID

    @staticmethod
    def is_valid_id(id_num: int) -> bool:
        return not Consts.is_empty_id(id_num)