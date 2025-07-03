from enum import Enum, auto


class ObjStatus(Enum):
    """ Various status effects that game objects can have. """
    EMPTY = 0  # Should never be used outside initialization
    ENVIRONMENT = auto()  # Special case used only by ENVIRONMENT objs
    ALIVE = auto()  # Default status used to indicate the absence of other status effects
    DESPAWNED = auto()  # Permamently removed from combat, cannot be source or target of events
    BANISHED = auto()  # Temporarily removed from combat, cannot be source or target of events
    CASTING = auto()  # to-do: document this
    CHANNELING = auto()  # to-do: document this
    ROOTED = auto()  # to-do: document this
    STUNNED = auto()  # to-do: document this

    @property
    def is_valid_source(self) -> bool:
        return not self in {
            ObjStatus.DESPAWNED,
            ObjStatus.BANISHED,
        }

    @property
    def is_valid_target(self) -> bool:
        return not self in {
            ObjStatus.ENVIRONMENT,
            ObjStatus.DESPAWNED,
            ObjStatus.BANISHED,
        }
