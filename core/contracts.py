"""Stable contracts shared by model providers and tools. Python 3.8 compatible."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

@dataclass
class ModelRequest:
    messages: List[Dict[str, str]]
    max_tokens: int = 512
    temperature: float = 0.2
    request_id: Optional[str] = None

@dataclass
class ModelResponse:
    text: str
    provider: str
    model: str
    elapsed_seconds: float = 0.0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = field(default_factory=dict)

class ModelProvider(Protocol):
    def generate(self, request: ModelRequest) -> ModelResponse: ...
    def health(self) -> Dict[str, Any]: ...

@dataclass
class ToolResult:
    ok: bool
    output: Any = None
    error: Optional[str] = None

@dataclass
class ToolSpec:
    name: str
    description: str
    risk: str = "read_only"
    requires_confirmation: bool = False
