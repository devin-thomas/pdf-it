"""Validated structures shared by the language-model and PDF layers."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DocumentBlock(BaseModel):
    """A paragraph or code block that preserves the original section order."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["paragraph", "code"]
    text: str = Field(min_length=1, max_length=8_000)


class DocumentSection(BaseModel):
    """One coherent section in the generated document."""

    model_config = ConfigDict(extra="forbid")

    heading: str = Field(min_length=1, max_length=120)
    blocks: list[DocumentBlock] = Field(min_length=1, max_length=12)
    callout: str | None = Field(default=None, max_length=350)


class DocumentPlan(BaseModel):
    """Provider-neutral editorial plan consumed by the deterministic renderer."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=140)
    subtitle: str | None = Field(default=None, max_length=220)
    summary: str | None = Field(default=None, max_length=600)
    sections: list[DocumentSection] = Field(min_length=1, max_length=12)
