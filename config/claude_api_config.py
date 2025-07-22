#!/usr/bin/env python3
"""
Claude API Configuration for LLM Testing Framework
"""

import os
from typing import Dict, Any

# Model configurations
MODELS = {
    "claude-3-5-sonnet": {
        "name": "claude-3-5-sonnet-20241022",
        "max_tokens": 200000,
        "recommended_max_tokens": 4000,
        "cost_per_input_token": 0.000003,
        "cost_per_output_token": 0.000015,
        "description": "High-performance model for complex analysis"
    },
    "claude-3-haiku": {
        "name": "claude-3-haiku-20240307",
        "max_tokens": 200000,
        "recommended_max_tokens": 4000,
        "cost_per_input_token": 0.00000025,
        "cost_per_output_token": 0.00000125,
        "description": "Fast, cost-effective model for basic analysis"
    }
}

# Default API settings
DEFAULT_CONFIG = {
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4000,
    "temperature": 0.1,
    "timeout": 60,
    "retry_attempts": 3,
    "retry_delay": 1.0
}

# Test condition configurations
CONDITION_CONFIGS = {
    "condition_1": {
        "name": "Source Data + Minimal Guidance",
        "data_type": "source",
        "guidance_type": "minimal",
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4000,
        "temperature": 0.1
    },
    "condition_2": {
        "name": "Source Data + Enhanced Guidance", 
        "data_type": "source",
        "guidance_type": "enhanced",
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4000,
        "temperature": 0.1
    },
    "condition_3": {
        "name": "Curated Data + Minimal Guidance",
        "data_type": "curated", 
        "guidance_type": "minimal",
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4000,
        "temperature": 0.1
    },
    "condition_4": {
        "name": "Curated Data + Enhanced Guidance",
        "data_type": "curated",
        "guidance_type": "enhanced", 
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4000,
        "temperature": 0.1
    }
}

def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return api_key

def get_condition_config(condition: str) -> Dict[str, Any]:
    """Get configuration for a specific test condition."""
    if condition not in CONDITION_CONFIGS:
        raise ValueError(f"Unknown condition: {condition}")
    return CONDITION_CONFIGS[condition].copy()

def estimate_cost(input_tokens: int, output_tokens: int, model: str = "claude-3-5-sonnet") -> float:
    """Estimate cost for API call."""
    if model not in MODELS:
        model = "claude-3-5-sonnet"
    
    model_config = MODELS[model]
    cost = (input_tokens * model_config["cost_per_input_token"] + 
            output_tokens * model_config["cost_per_output_token"])
    return cost

def validate_token_limits(prompt_length: int, model: str = "claude-3-5-sonnet") -> bool:
    """Check if prompt length is within model limits."""
    if model not in MODELS:
        model = "claude-3-5-sonnet"
    
    # Rough estimate: 4 characters per token
    estimated_tokens = prompt_length // 4
    max_tokens = MODELS[model]["max_tokens"]
    
    return estimated_tokens < (max_tokens * 0.8)  # Leave 20% buffer for response