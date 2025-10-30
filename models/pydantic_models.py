"""Pydantic models for the OnboardKit onboarding agent."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
# Removed all form-specific models (ProfileFormData, MarketplaceFormData, BankingFormData, SyncResponse)

class ToolResponse(BaseModel):
    """Generic response model for tool operations."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message about the result")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional response data")
    error: Optional[str] = Field(default=None, description="Error message if operation failed")