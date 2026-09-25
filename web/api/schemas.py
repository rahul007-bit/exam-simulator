from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class JumpRequest(BaseModel):
    task_num: int


class FlagRequest(BaseModel):
    task_num: Optional[int] = None


class StartRequest(BaseModel):
    preset: Optional[str] = None
    all_questions: Optional[bool] = False
    question_ids: Optional[List[str]] = None
    candidate_token: Optional[str] = None


class PresetSelectRequest(BaseModel):
    preset: str


class ClipboardRequest(BaseModel):
    text: str


class AdminLoginRequest(BaseModel):
    password: str


class AdminConfigRequest(BaseModel):
    default_preset: str


class CreateSessionInviteRequest(BaseModel):
    preset: Optional[str] = None


class ClientEventRequest(BaseModel):
    event_type: str
    data: Optional[Dict[str, Any]] = None


class RestoreSessionRequest(BaseModel):
    session_id: str


class SetResourceLimitRequest(BaseModel):
    max_concurrent_sessions: int


class TerminateResourceRequest(BaseModel):
    kind: str  # "docker" or "incus"
    node: str  # "mgmt", "node1", "node2", "node3", or "local"
    name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


class GeneratePresetRequest(BaseModel):
    count: int
    difficulty: Optional[str] = None
    domains: Optional[List[str]] = None
