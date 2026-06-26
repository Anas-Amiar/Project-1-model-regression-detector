"""
The AI feature under test: reads a customer support email and returns
a category + one-sentence summary as structured JSON.

Two modes:
- mock mode (default, no API key needed): returns a fake-but-plausible
  answer using simple keyword rules, so we can build and test everything
  else in the pipeline first.
- real mode: actually calls OpenAI using the prompt stored in /prompts.
"""

import json
import os
import yaml
from pydantic import BaseModel, ValidationError


class ClassificationResult(BaseModel):
    category: str
    summary: str


def load_prompt(version_id: str, prompts_dir: str = "prompts") -> dict:
    """Load a versioned prompt file, e.g. prompts/v1.yaml"""
    path = os.path.join(prompts_dir, f"{version_id}.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _mock_classify(email_text: str) -> ClassificationResult:
    """Fake classifier using simple keyword rules. Stand-in until we have an API key."""
    text = email_text.lower()
    if any(w in text for w in ["charge", "refund", "invoice", "payment", "billing"]):
        category = "billing"
    elif any(w in text for w in ["crash", "bug", "error", "won't load", "broken"]):
        category = "technical"
    elif any(w in text for w in ["password", "login", "log in", "account", "locked out"]):
        category = "account"
    else:
        category = "general"
    summary = email_text.strip().split(".")[0][:120]
    return ClassificationResult(category=category, summary=summary)


def _real_classify(email_text: str, prompt_config: dict) -> ClassificationResult:
    """Real classifier: calls OpenAI using the loaded prompt config."""
    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY from environment

    messages = [{"role": "system", "content": prompt_config["system_prompt"]}]
    for example in prompt_config.get("few_shot_examples", []):
        messages.append({"role": "user", "content": example["input"]})
        messages.append({"role": "assistant", "content": example["output"]})
    messages.append({"role": "user", "content": email_text})

    response = client.chat.completions.create(
        model=prompt_config.get("model", "gpt-4o-mini"),
        messages=messages,
        temperature=0,
    )
    raw = response.choices[0].message.content
    data = json.loads(raw)
    return ClassificationResult(**data)


def classify_email(
    email_text: str,
    prompt_version: str = "v1",
    use_mock: bool = True,
) -> ClassificationResult:
    """
    Main entry point. Set use_mock=False once you have an OPENAI_API_KEY
    set in your environment to use the real LLM.
    """
    if use_mock:
        return _mock_classify(email_text)

    prompt_config = load_prompt(prompt_version)
    try:
        return _real_classify(email_text, prompt_config)
    except (ValidationError, json.JSONDecodeError) as e:
        raise ValueError(f"LLM returned malformed output: {e}")


if __name__ == "__main__":
    sample_email = "I was charged twice for my subscription this month, please refund the duplicate charge."
    result = classify_email(sample_email, use_mock=True)
    print(f"Category: {result.category}")
    print(f"Summary:  {result.summary}")
