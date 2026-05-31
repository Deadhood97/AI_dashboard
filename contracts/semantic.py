from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.base import schema_extra


class SemanticUnderstanding(BaseModel):
    model_config = schema_extra("semantic_understanding")

    dataset_domain: str = Field(
        description="The likely business or analytical domain of the dataset."
    )
    primary_entities: list[str] = Field(
        description="Main real-world entities represented in the dataset."
    )
    important_dimensions: list[str] = Field(
        description="Categorical, temporal, or segmentation fields useful for slicing data."
    )
    important_metrics: list[str] = Field(
        description="Numeric measures or KPIs that are analytically important."
    )
    analytical_goals: list[str] = Field(
        description="High-value analytical goals that fit the dataset."
    )
    suggested_questions: list[str] = Field(
        description="Specific questions that can likely be answered from the dataset."
    )
