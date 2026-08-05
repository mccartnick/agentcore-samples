"""Configure the OpenAI Agents SDK for an OpenAI model on Amazon Bedrock."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BedrockOpenAIRuntime:
    """Resolved model settings used by every agent in the team."""

    model: str
    region: str


def configure_bedrock_openai() -> BedrockOpenAIRuntime:
    """Install a Bedrock-backed OpenAI client as the Agents SDK default."""
    from agents import set_default_openai_client, set_tracing_disabled
    from aws_bedrock_token_generator import provide_token
    from openai import AsyncOpenAI

    region = os.getenv("AWS_REGION", "us-east-1")
    model = os.getenv("BEDROCK_OPENAI_MODEL", "openai.gpt-5.5")
    base_url = f"https://bedrock-mantle.{region}.api.aws/openai/v1"

    set_default_openai_client(
        AsyncOpenAI(api_key=provide_token(region=region), base_url=base_url),
        use_for_tracing=False,
    )
    set_tracing_disabled(True)
    return BedrockOpenAIRuntime(model=model, region=region)
