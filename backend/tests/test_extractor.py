import pytest
from fastapi import HTTPException
import json
import httpx

def test_no_consent_returns_manual_needs_review_without_skills(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")

    from backend.extractor import extract_document

    result = extract_document(
        source_type="jd",
        source_file="jd_a.docx",
        source_text=(
            "Company: Synthetic Practice Co\n"
            "Role: Junior Developer\n"
            "Required: Python\n"
            "Preferred: SQL"
        ),
        consent=False,
    )

    assert result.source_type == "jd"
    assert result.source_file == "jd_a.docx"
    assert result.review_status == "needs_review"
    assert result.extraction_method == "manual"
    assert result.skills == []
    assert result.requirement_groups == []
    assert result.source_text.startswith("Company: Synthetic Practice Co")
    assert result.warnings


def test_consent_without_api_key_raises_503(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "")

    from backend.extractor import extract_document

    with pytest.raises(HTTPException) as error:
        extract_document(
            source_type="jd",
            source_file="jd_a.docx",
            source_text="Role: Synthetic test",
            consent=True,
        )

    assert error.value.status_code == 503


def test_mocked_groq_response_returns_needs_review_with_server_ids(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-only-not-a-real-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")

    import backend.extractor as extractor

    source_text = (
        "Company: Synthetic Practice Co\n"
        "Role: Junior Developer\n"
        "Required: Python\n"
        "Preferred: SQL"
    )

    # This is the provider's proposal: it contains no IDs or review status.
    proposal = {
        "company": "Synthetic Practice Co",
        "role": "Junior Developer",
        "name": "",
        "email": "",
        "skills": [
            {
                "skill_name": "Python",
                "category_code": "COD",
                "evidence": "Required: Python",
                "confidence": "medium",
                "source_page": None,
                "claim_status": "claimed",
            },
            {
                "skill_name": "SQL",
                "category_code": "SQL",
                "evidence": "Preferred: SQL",
                "confidence": "medium",
                "source_page": None,
                "claim_status": "claimed",
            },
        ],
        "requirement_groups": [
            {
                "skill_names": ["Python"],
                "operator": "AND",
                "requirement_type": "mandatory",
                "evidence": "Required: Python",
            },
            {
                "skill_names": ["SQL"],
                "operator": "AND",
                "requirement_type": "preferred",
                "evidence": "Preferred: SQL",
            },
        ],
        "education": [],
        "projects": [],
        "experience": [],
        "internships": [],
        "hackathons": [],
        "certifications": [],
        "achievements": [],
    }

    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    response = httpx.Response(
        200,
        json={
            "choices": [
                {"message": {"content": json.dumps(proposal)}}
            ]
        },
        request=httpx.Request("POST", endpoint),
    )
    captured = {}

    def fake_post(url, *, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json
        captured["timeout"] = timeout
        return response

    monkeypatch.setattr(httpx, "post", fake_post)

    result = extractor.extract_document(
        source_type="jd",
        source_file="jd_a.docx",
        source_text=source_text,
        consent=True,
    )

    assert result.review_status == "needs_review"
    assert result.extraction_method == "groq"
    assert result.source_text == source_text
    assert result.company == "Synthetic Practice Co"
    assert result.role == "Junior Developer"

    assert [skill.skill_name for skill in result.skills] == ["Python", "SQL"]
    assert all(skill.source_type == "document" for skill in result.skills)
    assert all(skill.source_id == result.id for skill in result.skills)
    assert len({skill.skill_id for skill in result.skills}) == 2
    assert result.skills[0].skill_id != "jd-python"

    assert [group.requirement_type for group in result.requirement_groups] == [
        "mandatory",
        "preferred",
    ]
    assert all(
        skill_id in {skill.skill_id for skill in result.skills}
        for group in result.requirement_groups
        for skill_id in group.skill_ids
    )

    assert captured["url"] == endpoint
    assert captured["headers"]["Authorization"] == (
        "Bearer test-only-not-a-real-key"
    )
    assert captured["body"]["model"] == "openai/gpt-oss-20b"
    assert captured["body"]["response_format"]["type"] == "json_schema"
    assert captured["body"]["response_format"]["json_schema"]["strict"] is True
    system_prompt = captured["body"]["messages"][0]["content"]
    assert "programming languages such as Python map to COD" in system_prompt
    assert "SWE is for software engineering practices" in system_prompt
    assert "unfamiliar or ambiguous skills" in system_prompt
    assert "confidence 'low' and claim_status 'needs_review'" in system_prompt
    assert "use OTHER if no category fits clearly" in system_prompt
    assert "skill_names must be copied exactly from skill_name fields" in system_prompt
    assert captured["timeout"] <= 45


def test_unknown_requirement_skill_name_reports_safe_provider_error(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-only-not-a-real-key")

    import backend.extractor as extractor

    proposal = extractor.Proposal(
        company="Synthetic Practice Co",
        role="Data Engineer",
        name="",
        email="",
        skills=[
            extractor.ProposedSkill(
                skill_name="Polars",
                category_code="OTHER",
                evidence="Required: Polars",
                confidence="low",
                source_page=None,
                claim_status="needs_review",
            )
        ],
        requirement_groups=[
            extractor.ProposedRequirement(
                skill_names=["Polars DataFrame"],
                operator="AND",
                requirement_type="mandatory",
                evidence="Required: Polars",
            )
        ],
        education=[],
        projects=[],
        experience=[],
        internships=[],
        hackathons=[],
        certifications=[],
        achievements=[],
    )
    monkeypatch.setattr(extractor, "_load_proposal", lambda **kwargs: proposal)

    with pytest.raises(HTTPException) as error:
        extractor.extract_document(
            source_type="jd",
            source_file="synthetic_jd.txt",
            source_text="Required: Polars",
            consent=True,
        )

    assert error.value.status_code == 502
    assert "Polars DataFrame" in error.value.detail
