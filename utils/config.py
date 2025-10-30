"""Configuration for the OnboardKit onboarding agent."""

from typing import Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Configuration(BaseModel):
    """Pydantic configuration for the onboarding agent."""
    
    # LLM Configuration
    model: str = Field(default="gpt-4o", description="The language model to use")
    max_tokens: int = Field(default=1500, ge=1, le=4000, description="Maximum tokens to generate")
    llm_timeout: float = Field(default=45.0, gt=0, description="LLM timeout in seconds")
    
    @validator('model')
    def validate_model(cls, v):
        """Validate that the model is supported."""
        supported_models = ["gpt-4o", "gpt-4", "gpt-3.5-turbo"]
        if v not in supported_models:
            raise ValueError(f"Model must be one of {supported_models}")
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        """Validate max_tokens is reasonable."""
        if v < 1:
            raise ValueError("max_tokens must be at least 1")
        if v > 4000:
            raise ValueError("max_tokens cannot exceed 4000")
        return v
    
    @validator('llm_timeout')
    def validate_timeout(cls, v):
        """Validate timeout is positive."""
        if v <= 0:
            raise ValueError("llm_timeout must be positive")
        return v
    
    @classmethod
    def from_runnable_config(cls, config=None) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig object."""
        return cls()

    def create_llm(self):
        """Create an LLM instance with the configured parameters."""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=self.model,
            max_tokens=self.max_tokens,
            timeout=self.llm_timeout
        )
    
    class Config:
        """Pydantic configuration."""
        # Changed env prefix to be generic
        env_prefix = 'ONBOARDKIT_'