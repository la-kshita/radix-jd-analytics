from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CategoryCode = Literal[
    "COD",
    "DSA",
    "OOD",
    "APTI",
    "COMM",
    "AI",
    "CLOUD",
    "SQL",
    "SWE",
    "SYSD",
    "NETW",
    "OS",
    "OTHER",
]


def _normalize_whitespace(value: str) -> str:
    """Normalize whitespace only, preserving the actual source text elsewhere."""
    return " ".join(value.split())


class Skill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str = Field(min_length=1)
    skill_name: str = Field(min_length=1)
    category_code: CategoryCode
    evidence: str = Field(min_length=1)
    confidence: Literal["high", "medium", "low"]
    source_type: Literal["document", "manual", "hypothetical"]
    source_id: str | None
    source_page: int | None = Field(default=None, ge=1)
    claim_status: Literal["claimed", "needs_review"]


class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(min_length=1)
    skill_ids: list[str] = Field(min_length=1)
    operator: Literal["AND", "OR"]
    requirement_type: Literal["mandatory", "preferred", "unspecified"]
    evidence: str = Field(min_length=1)

    @model_validator(mode="after")
    def skill_ids_are_unique(self):
        if len(self.skill_ids) != len(set(self.skill_ids)):
            raise ValueError("A requirement group cannot repeat a skill ID")
        return self


class Extraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["TEAM-V1"]
    id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    source_type: Literal["jd", "resume"]
    source_file: str = Field(min_length=1)
    source_text: str = Field(min_length=1)

    company: str | None = None
    role: str | None = None
    name: str = ""
    email: str = ""

    skills: list[Skill] = Field(default_factory=list)
    requirement_groups: list[Requirement] = Field(default_factory=list)

    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    internships: list[str] = Field(default_factory=list)
    hackathons: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    review_status: Literal["needs_review", "reviewed"]
    extraction_method: Literal["groq", "manual", "rules"]
    warnings: list[str] = Field(default_factory=list)

    @field_validator("source_file")
    @classmethod
    def source_file_must_be_a_basename(cls, value: str) -> str:
        if "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("source_file must be a filename, not a path")
        return value

    @model_validator(mode="after")
    def references_and_quotes_must_match_source(self):
        skill_ids = [skill.skill_id for skill in self.skills]
        if len(skill_ids) != len(set(skill_ids)):
            raise ValueError("Skill IDs must be unique within an extraction")

        requirement_ids = [
            group.requirement_id for group in self.requirement_groups
        ]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise ValueError("Requirement IDs must be unique within an extraction")

        if self.source_type == "resume" and self.requirement_groups:
            raise ValueError("Resume extractions cannot have requirement groups")

        known_skill_ids = set(skill_ids)
        source_text = _normalize_whitespace(self.source_text)

        for skill in self.skills:
            if skill.source_type == "document":
                if skill.source_id != self.id:
                    raise ValueError(
                        f"Document skill {skill.skill_id} must reference "
                        "this extraction's source ID"
                    )
                if _normalize_whitespace(skill.evidence) not in source_text:
                    raise ValueError(
                        f"Evidence for skill {skill.skill_id} is not in source text"
                    )

        for group in self.requirement_groups:
            unknown_ids = set(group.skill_ids) - known_skill_ids
            if unknown_ids:
                raise ValueError(
                    f"Requirement {group.requirement_id} references unknown "
                    f"skill IDs: {sorted(unknown_ids)}"
                )
            if _normalize_whitespace(group.evidence) not in source_text:
                raise ValueError(
                    f"Evidence for requirement {group.requirement_id} "
                    "is not in source text"
                )

        return self