from enum import Enum

class Priority(int, Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

class ErrorType(str, Enum):
    NETWORK_ERROR = "NetworkError"
    PARSE_ERROR = "ParseError"
    ACCESS_DENIED = "AccessDenied"
    RATE_LIMITED = "RateLimited"
    NONE = "None"

class Status(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"