from enum import Enum, auto

class MDState(Enum):
    RUNNING_PRIOR = auto()
    RUNNING_MANUAL = auto()
    RUNNING_AUTO = auto()
    NOT_RUNNING = auto()
    NOT_RESPONDING = auto()

class ControllerState(Enum):
    MANUAL = auto()
    AUTO = auto()
