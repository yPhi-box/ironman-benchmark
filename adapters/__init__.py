from .base import MemoryAdapter
from .oc import OCAdapter
from .hms import HMSAdapter
from .grep import GrepAdapter

ADAPTERS = {
    "oc": OCAdapter,
    "hms": HMSAdapter,
    "grep": GrepAdapter,
}
