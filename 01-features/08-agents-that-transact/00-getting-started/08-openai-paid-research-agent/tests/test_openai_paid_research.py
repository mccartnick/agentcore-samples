from openai_paid_research import build_research_team


def fake_paid_source() -> str:
    return '{"payment_made": true, "body": "premium evidence"}'


def test_only_the_premium_analyst_has_payment_authority() -> None:
    team = build_research_team(fake_paid_source, model="openai.gpt-5.5")

    assert team.lead.name == "Research lead"
    assert team.public_analyst.name == "Public evidence analyst"
    assert team.premium_analyst.name == "Premium evidence analyst"
    assert [tool.name for tool in team.lead.tools] == [
        "research_public_evidence",
        "research_premium_evidence",
    ]
    assert team.public_analyst.tools == []
    assert [tool.name for tool in team.premium_analyst.tools] == ["fetch_approved_premium_source"]
