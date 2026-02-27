from dataclasses import dataclass, field
from enum import Enum

class opcodeCommand(Enum):
    WRITE = '0' #0x0000, Wait then Execute write value to address
    WAIT = 'A0' #0x00A0, Wait for READY (control Board) / SYNC3(other boards)
    LOOP = 'C0' #0x00C0, Wait, then loop to line# (address) N times (value).
    END = 'FF' #0x00FF, End of experiment, Set Start bit to 0 

@dataclass
class Step:
    canonical_name: str
    setpoint: float
    opcode: opcodeCommand
    abs_time_ms: float
    priority: int = 0

@dataclass
class Module:
    name: str
    steps: list[Step] = field(default_factory=list)

    def add_step(self, canonical_name: str, setpoint: float, opcode: opcodeCommand, abs_time_ms: float, priority: int = 0):
        step = Step(canonical_name, setpoint, opcode, abs_time_ms, priority)
        self.steps.append(step)
    