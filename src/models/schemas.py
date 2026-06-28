from typing import List, Optional

from pydantic import BaseModel, Field


class IncidentInput(BaseModel):
    logs: str = Field(description="Raw incident logs")
    image_description: Optional[str] = Field(default=None)
    image_data_uri: Optional[str] = Field(default=None, description="Optional base64 data URI for an uploaded incident image")


class VisionReport(BaseModel):
    summary: str
    key_observations: List[str]


class Hypothesis(BaseModel):
    hypothesis_id: str
    description: str


class UniverseResult(BaseModel):
    universe_id: str
    hypothesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str]
    recommended_action: str
    rollback: str
    missing_evidence: List[str] = Field(default_factory=list)


class FinalIncidentReport(BaseModel):
    winning_universe: str
    ranked_universes: List[UniverseResult] = Field(
        min_length=4,
        max_length=4,
        description=(
            "Exactly four ranked universes. Must include every explored universe_id "
            "exactly once and must be sorted by confidence descending."
        ),
    )
    overall_summary: str
    recommended_next_steps: List[str]
