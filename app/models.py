"""
Pydantic models for request/response validation.

All data structures for the ContextDiff API are defined here with strict typing.
"""

from enum import Enum
from typing import Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator, model_validator


class SensitivityLevel(str, Enum):
    """Sensitivity level for semantic analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ChangeType(str, Enum):
    """Type of semantic change detected."""
    FACTUAL = "FACTUAL"
    TONE = "TONE"
    OMISSION = "OMISSION"
    ADDITION = "ADDITION"
    FORMATTING = "FORMATTING"


class ChangeSeverity(str, Enum):
    """Severity level of a detected change."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SemanticChangeLevel(str, Enum):
    """Overall semantic change classification."""
    NONE = "NONE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    CRITICAL = "CRITICAL"
    FATAL = "FATAL"


class TextSpan(BaseModel):
    """
    Represents a span of text with its position and surrounding context.
    
    Attributes:
        text: The actual text content.
        start: Start character position (0-indexed).
        end: End character position (exclusive).
        context_before: Up to 30 characters before the span (for validation).
        context_after: Up to 30 characters after the span (for validation).
    """
    text: str = Field(..., description="The text content of this span")
    start: int = Field(..., ge=0, description="Start position in the original text")
    end: int = Field(..., ge=0, description="End position in the original text")
    context_before: str = Field(default="", description="Context before span for validation")
    context_after: str = Field(default="", description="Context after span for validation")
    
    @validator("end")
    def end_must_be_after_start(cls, v: int, values: dict) -> int:
        """Validate that end position is after start position."""
        if "start" in values and v < values["start"]:
            raise ValueError("end must be greater than or equal to start")
        return v


class ChangeItem(BaseModel):
    """
    Represents a single semantic change detected between texts.
    
    Attributes:
        id: Unique identifier for this change.
        type: Category of the change.
        severity: How critical this change is.
        description: Human-readable explanation of the change.
        original_span: Location and content in the original text.
        generated_span: Location and content in the generated text.
        reasoning: Detailed chain-of-thought explanation.
    """
    
    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, values: Any) -> Any:
        """Auto-correct LLM case errors and map severity values."""
        if isinstance(values, dict):
            # Uppercase type field (e.g., "Factual" -> "FACTUAL")
            if values.get('type'):
                values['type'] = values['type'].upper()
            # Map and normalize severity field
            if values.get('severity'):
                severity_lower = values['severity'].lower().strip()
                # Map LLM variations to valid enum values
                severity_map = {
                    'minor': 'info',
                    'low': 'info',
                    'none': 'info',
                    'moderate': 'warning',
                    'medium': 'warning',
                    'high': 'critical',
                    'fatal': 'critical',
                    'severe': 'critical',
                    # Already valid values
                    'info': 'info',
                    'warning': 'warning',
                    'critical': 'critical',
                }
                values['severity'] = severity_map.get(severity_lower, 'warning')
        return values
    
    id: UUID = Field(default_factory=uuid4, description="Unique change identifier")
    type: ChangeType = Field(..., description="Category of semantic change")
    severity: ChangeSeverity = Field(..., description="Severity level of the change")
    description: str = Field(..., min_length=1, description="Brief explanation of the change")
    original_span: TextSpan = Field(..., description="Span in the original text")
    generated_span: TextSpan = Field(..., description="Span in the generated text")
    reasoning: str = Field(..., min_length=1, description="Detailed reasoning for this classification")


class DiffSummary(BaseModel):
    """
    High-level summary of the semantic analysis.
    
    Attributes:
        is_safe: Whether the generated text is semantically safe to use.
        risk_score: Numerical risk score from 0 (identical) to 100 (completely different).
        semantic_change_level: Categorical assessment of overall change magnitude.
    """
    is_safe: bool = Field(..., description="Whether the text is safe to use")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score from 0-100")
    semantic_change_level: SemanticChangeLevel = Field(..., description="Overall change classification")


class CompareRequest(BaseModel):
    """
    Request payload for semantic text comparison.
    
    Attributes:
        original_text: The source/reference text.
        generated_text: The text to compare against the original.
        sensitivity: Analysis sensitivity level (affects filtering of minor changes).
        premium_mode: Use premium model (gpt-4o) instead of default (gpt-4o-mini).
    """
    original_text: str = Field(
        ..., 
        min_length=1, 
        max_length=50000,
        description="The original/reference text"
    )
    generated_text: str = Field(
        ..., 
        min_length=1, 
        max_length=50000,
        description="The generated text to compare"
    )
    sensitivity: SensitivityLevel = Field(
        default=SensitivityLevel.MEDIUM,
        description="Analysis sensitivity: low (only critical), medium (balanced), high (all changes)"
    )
    premium_mode: bool = Field(
        default=False,
        description="Use premium model (gpt-4o) for higher accuracy. Default uses gpt-4o-mini."
    )
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "original_text": "The product will be available in Q1 2024.",
                "generated_text": "The product might be available in early 2024.",
                "sensitivity": "medium"
            }
        }


class DiffResponse(BaseModel):
    """
    Complete response from semantic difference analysis.
    
    Attributes:
        summary: High-level assessment of the comparison.
        changes: List of individual changes detected (empty if no changes).
    """
    summary: DiffSummary = Field(..., description="Summary of the semantic analysis")
    changes: list[ChangeItem] = Field(
        default_factory=list,
        description="Detailed list of detected changes"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "summary": {
                    "is_safe": False,
                    "risk_score": 45,
                    "semantic_change_level": "MODERATE"
                },
                "changes": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "type": "FACTUAL",
                        "severity": "warning",
                        "description": "Certainty level changed from definite to uncertain",
                        "original_span": {
                            "text": "will be available",
                            "start": 12,
                            "end": 28
                        },
                        "generated_span": {
                            "text": "might be available",
                            "start": 12,
                            "end": 30
                        },
                        "reasoning": "The modal verb changed from 'will' (definite) to 'might' (uncertain), weakening the commitment."
                    }
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
