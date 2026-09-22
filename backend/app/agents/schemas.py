from pydantic import BaseModel, Field


class RoundScore(BaseModel):
    """Structured evaluator scoring for a single debater's argument.

    Sub-score ranges follow the PRD spec: logical_strength 0-3, evidence_quality
    0-3, clarity 0-2, counterargument_handling 0-2 (total 0-10). The total is
    always computed in code from these parsed sub-scores — never trusted as a
    bare float from the model, unlike the PRD's `float(response.content)`
    approach which throws on any non-numeric LLM output.
    """

    logical_strength: float = Field(ge=0, le=3, description="Strength and validity of the logical reasoning, 0-3")
    evidence_quality: float = Field(ge=0, le=3, description="Quality/relevance of evidence and citations used, 0-3")
    clarity: float = Field(ge=0, le=2, description="Clarity and persuasiveness of the writing, 0-2")
    counterargument_handling: float = Field(
        ge=0, le=2, description="How well the argument anticipates/rebuts the opposing side, 0-2"
    )
    feedback: str = Field(description="One or two sentences of concrete feedback for this argument")

    @property
    def total(self) -> float:
        return (
            self.logical_strength
            + self.evidence_quality
            + self.clarity
            + self.counterargument_handling
        )
