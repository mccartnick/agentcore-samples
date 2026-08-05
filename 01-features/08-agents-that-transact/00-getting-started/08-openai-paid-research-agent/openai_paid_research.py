"""Budget-bounded multi-agent research with AgentCore Payments and OpenAI."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from agents import Agent, Runner
from bedrock_agentcore.payments import PaymentManager
from bedrock_openai import configure_bedrock_openai
from dotenv import load_dotenv
from payment import PaymentConfig, create_payment_session, fetch_x402

SHARED_ENV = Path(__file__).resolve().parent.parent / ".env"
LOCAL_ENV = Path(__file__).resolve().parent / ".env"

LEAD_INSTRUCTIONS = """You are the research lead. Delegate to the public
analyst first. Use the premium analyst only for a material remaining evidence
gap. Distinguish public evidence from paid evidence in the final answer."""

PUBLIC_INSTRUCTIONS = """You are the public evidence analyst. Analyze public
evidence supplied in the request, identify what it supports, and state any
material remaining evidence gap. You cannot make payments."""

PREMIUM_INSTRUCTIONS = """You are the premium evidence analyst. Use the
application-bound paid source only when asked to close a specific evidence gap.
Report what the paid evidence added and whether the purchase succeeded."""


@dataclass(frozen=True)
class ResearchTeam:
    """The manager and two bounded specialists."""

    lead: Agent
    public_analyst: Agent
    premium_analyst: Agent


def build_research_team(fetch_paid_source: Callable[[], str], model: str) -> ResearchTeam:
    """Build the manager pattern and isolate payment authority.

    TODO:
    1. Create a public analyst with no payment tools.
    2. Wrap ``fetch_paid_source`` with ``agents.function_tool`` and give it only
       to the premium analyst.
    3. Expose both specialists to the lead with ``Agent.as_tool()``.
    4. Return all three agents in ``ResearchTeam``.

    Use the tool names asserted in ``tests/test_openai_paid_research.py``.
    """
    raise NotImplementedError("Implement build_research_team in openai_paid_research.py")


async def run_research(team: ResearchTeam, query: str) -> str:
    """Run the manager and return its final response."""
    result = await Runner.run(team.lead, query)
    return str(result.final_output)


def load_environment() -> None:
    """Load shared payment resources, then tutorial-specific overrides."""
    load_dotenv(SHARED_ENV)
    load_dotenv(LOCAL_ENV, override=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("query", help="Financial research question and any public evidence")
    return result


def main(argv: Sequence[str] | None = None) -> None:
    """Create a fresh session and run the research team."""
    load_environment()
    args = parser().parse_args(argv)
    runtime = configure_bedrock_openai()
    config = PaymentConfig.from_env()
    manager = PaymentManager(
        payment_manager_arn=config.manager_arn,
        region_name=config.region,
    )
    payment_session_id = create_payment_session(manager, config)

    def fetch_approved_premium_source() -> str:
        """Purchase and return the one source selected by the application."""
        return fetch_x402(manager, config, payment_session_id)

    team = build_research_team(fetch_approved_premium_source, runtime.model)
    print(asyncio.run(run_research(team, args.query)))


if __name__ == "__main__":
    main()
