"""Data shapes used everywhere: chat messages, memory records, match results."""
from typing import Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # "user" or "model"
    text: str


class InterviewTurn(BaseModel):
    """What Gemini returns on each interview step."""
    reply: str = Field(description="The next question or a short closing message, in the user's language")
    done: bool = Field(description="True once enough detail has been collected or the user wants to stop")


class MemoryRecord(BaseModel):
    """A structured memory pulled out of the interview by Gemini."""
    id: Optional[str] = None
    owner_name: Optional[str] = Field(default=None, description="The user's own real first name, if given")
    my_nicknames: list[str] = Field(default_factory=list, description="Names/nicknames the OTHER person would know the user by")
    their_nicknames: list[str] = Field(default_factory=list, description="Names/nicknames/partial names of the person being searched for, with likely spelling variants")
    year_start: Optional[int] = Field(default=None, description="Earliest year of the shared memory")
    year_end: Optional[int] = Field(default=None, description="Latest year of the shared memory")
    city: Optional[str] = Field(default=None, description="City, normalised (e.g. 'Jaipur')")
    places: list[str] = Field(default_factory=list, description="Specific places: parks, colonies, streets, landmarks")
    institutions: list[str] = Field(default_factory=list, description="Schools, tuition classes, colleges, offices")
    my_age_then: Optional[int] = None
    their_age_then: Optional[int] = None
    shared_activities: list[str] = Field(default_factory=list)
    other_people: list[str] = Field(default_factory=list, description="Other friends/teachers both would know")
    self_description: str = Field(default="", description="How the other person would remember the user")
    memory_summary: str = Field(default="", description="2-4 sentence neutral summary of the shared memory")
    secret_detail: str = Field(default="", description="One thing only the two of them would know. Never shown to anyone.")


class JudgeResult(BaseModel):
    """Gemini's verdict on whether two memories are about the same people."""
    probability: float = Field(description="0 to 1: chance these two records describe the same shared past")
    evidence: list[str] = Field(description="Specific points that agree")
    conflicts: list[str] = Field(description="Specific points that disagree")
    verification_questions: list[str] = Field(description="2-3 yes/no questions to ask the OTHER person, that do not reveal private details")


class SecretCheck(BaseModel):
    same: bool = Field(description="True if both secret details describe the same event/thing")
    reason: str
