from pydantic import BaseModel, ConfigDict, Field


class GeneratedKnowledgeAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_supported: bool
    answer: str = Field(max_length=1200)


class RagAnswer(BaseModel):
    text: str
    source_labels: list[str]
