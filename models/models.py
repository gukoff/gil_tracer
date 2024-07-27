from enum import Enum
from typing import Optional
from pydantic import BaseModel


class ThreadStats(BaseModel):
    tid: int
    held: float
    waited: float


class ThreadState(int, Enum):
    """Values here correspond to the values in the raw perf events"""

    wait = 0  # waits for GIL (entered take_gil)
    hold = 1  # holds GIL (exited take_gil)
    free = 2  # dropped GIL (entered drop_gil)


class Event(BaseModel):
    timestamp: int  # nanoseconds since boot, see CLOCK_BOOTTIME
    thread_id: int
    location: Optional[str]
    new_state: ThreadState
