# Build Exercise: Budget-Bounded Paid Research

Treat this tutorial like a small take-home exercise. The configuration, model
client, CLI shell, types, and tests are provided. Your job is to implement the
three boundaries that make the example interesting.

## Problem

Build a three-agent research team with the OpenAI Agents SDK:

- A research lead delegates work and writes the final answer.
- A public evidence analyst can analyze supplied public evidence but cannot pay.
- A premium evidence analyst can buy exactly one application-approved x402
  source.

The application creates a fresh AgentCore payment session for each run. The
session, rather than a prompt, enforces the maximum spend and expiry.

## Constraints

- Use the Bedrock-hosted OpenAI model configured in `bedrock_openai.py`.
- Do not add a direct OpenAI API fallback or `BEDROCK_OPENAI_ENABLED` flag.
- Do not accept a URL as a model-tool argument.
- Give the payment function only to the premium analyst.
- Use the existing wallet instrument from Tutorial 00.
- Never read or commit wallet-provider credentials.
- Keep the implementation small enough to understand in one sitting.

## Start Here

```bash
cd 01-features/08-agents-that-transact/00-getting-started/08-openai-paid-research-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest -q
```

The four starter tests fail with `NotImplementedError`. Implement one task at a
time and rerun the relevant test.

## Task 1: Create the Payment Session

Open `payment.py` and implement `create_payment_session`.

```bash
pytest -q tests/test_payment.py::test_creates_a_budget_bounded_session
```

Hints:

- The AgentCore SDK method is `manager.create_payment_session(...)`.
- Use `config.user_id`, `config.budget`, and `config.expiry_minutes`.
- The limit shape is asserted in the test.
- Return only `paymentSessionId`.

## Task 2: Complete the x402 Exchange

Implement `fetch_x402` in `payment.py`.

```bash
pytest -q tests/test_payment.py
```

The minimum flow is:

1. Send an HTTPS GET to the bound URL.
2. If it returns `402`, pass the full response to
   `manager.generate_payment_header(...)`.
3. Retry the same URL with the returned header.
4. Return JSON describing the status, body, and whether payment succeeded.

Use one idempotency token for the payment attempt. Do not follow redirects.

## Task 3: Build the Agent Team

Implement `build_research_team` in `openai_paid_research.py`.

```bash
pytest -q tests/test_openai_paid_research.py
```

Hints:

- Import `function_tool` from `agents`.
- Wrap the supplied `fetch_paid_source` callable.
- Give that tool only to the premium analyst.
- Expose the specialists to the lead with `Agent.as_tool(...)`.
- Use the exact agent and tool names asserted by the test.

## Run Offline Checks

```bash
pytest -q
ruff check .
ruff format --check .
```

## Run Live

Tutorial 00 must already have created and delegated a wallet instrument. This
exercise reuses `PAYMENT_MANAGER_ARN`, `INSTRUMENT_ID`, `USER_ID`, and
`AWS_REGION` from the shared `../.env`; it does not need the provider's API key
or wallet secret.

```bash
python openai_paid_research.py \
  "Assess the supplied public evidence and buy the approved source only if it closes a material gap."
```

Each run creates a new short-lived session. The live path spends testnet USDC
when the approved endpoint requests payment.

## Definition of Done

- All four tests pass.
- The lead has specialist tools but no payment tool.
- The public analyst has no payment tool.
- The premium analyst has exactly one bound payment tool.
- A `402` response is settled and retried once.
- A non-`402` response does not call AgentCore Payments.
- The live output distinguishes public from paid evidence.

## Stretch Goals

- Add explicit human approval before the paid tool call.
- Report remaining session budget after a purchase.
- Add bounded retries for transient testnet settlement failures.
- Add public-source retrieval after the Bedrock Responses endpoint supports the
  current hosted web-search schema.
