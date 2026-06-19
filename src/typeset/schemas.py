"""Validated structures shared by the language-model and PDF layers."""

from pydantic import BaseModel, ConfigDict, Field


class DocumentSection(BaseModel):
    """One coherent section in the generated document."""

    model_config = ConfigDict(extra="forbid")

    heading: str = Field(min_length=1, max_length=120)
    paragraphs: list[str] = Field(min_length=1, max_length=8)
    callout: str | None = Field(default=None, max_length=350)


class DocumentPlan(BaseModel):
    """Provider-neutral editorial plan consumed by the deterministic renderer."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=140)
    subtitle: str | None = Field(default=None, max_length=220)
    summary: str | None = Field(default=None, max_length=600)
    sections: list[DocumentSection] = Field(min_length=1, max_length=12)
