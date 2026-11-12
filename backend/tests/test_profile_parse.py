"""Profile JSON extracted from a non-streaming Ollama response. No database."""

from services import profile_builder


def _profile_from_response(monkeypatch, response: str) -> dict:
    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": response}

    monkeypatch.setattr(profile_builder.requests, "post", lambda *_a, **_k: _Response())
    return profile_builder._call_ollama_for_profile("resume text")


def test_profile_json_survives_braces_inside_strings(monkeypatch):
    """A } inside a string must not end the object early, and quoted years stay numeric."""
    response = """```json
{
  "study_style": "use } in examples",
  "name": "Ada Lovelace",
  "experience_years": "8 years",
  "target_roles": ["Backend engineer"]
}
```"""

    profile = _profile_from_response(monkeypatch, response)

    assert profile["name"] == "Ada Lovelace"
    assert profile["study_style"] == "use } in examples"
    assert profile["experience_years"] == 8
    assert profile["target_roles"] == ["Backend engineer"]


def test_profile_json_ignores_a_leading_think_block(monkeypatch):
    response = """<think>
The resume mentions {python} and a } that is not JSON.
</think>
{"name": "Grace", "current_role": "Engineer", "experience_years": 6}
"""

    profile = _profile_from_response(monkeypatch, response)

    assert profile["name"] == "Grace"
    assert profile["current_role"] == "Engineer"
    assert profile["experience_years"] == 6
    assert profile["target_roles"] == []
