"""Fail-closed policy checks for tool operations."""
from dataclasses import dataclass

RISK_LEVELS = ("read_only", "reversible_write", "external_or_destructive")

@dataclass
class Operation:
    tool_name: str
    risk: str
    target: str = ""
    reason: str = ""

class PolicyDenied(PermissionError):
    pass

class Policy:
    def __init__(self, allowed_tools=None, allow_writes=False):
        self.allowed_tools = set(allowed_tools or [])
        self.allow_writes = bool(allow_writes)

    def check(self, operation, confirmed=False):
        if operation.risk not in RISK_LEVELS:
            raise PolicyDenied("Unknown risk level; operation denied.")
        if operation.tool_name not in self.allowed_tools:
            raise PolicyDenied("Tool is not allowlisted.")
        if operation.risk == "reversible_write" and not self.allow_writes:
            raise PolicyDenied("Write operations are disabled.")
        if operation.risk == "external_or_destructive" and not confirmed:
            raise PolicyDenied("Explicit confirmation is required.")
        return True
