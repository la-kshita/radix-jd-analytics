from fastapi import HTTPException
from pydantic import ValidationError

from backend.models import Extraction


def review_extraction(
    original: Extraction,
    submitted: Extraction,
) -> Extraction:
    """Validate corrections against the stored extraction and create a revision."""
    if submitted.id != original.id:
        raise HTTPException(status_code=404, detail="Extraction was not found.")

    if submitted.revision != original.revision:
        raise HTTPException(
            status_code=409,
            detail="This extraction has changed. Reload it before reviewing.",
        )

    if (
        submitted.schema_version != original.schema_version
        or submitted.source_type != original.source_type
        or submitted.source_file != original.source_file
        or submitted.source_text != original.source_text
    ):
        raise HTTPException(
            status_code=422,
            detail="The original source and its identity cannot be changed.",
        )

    try:
        corrected = Extraction.model_validate(submitted.model_dump())
    except ValidationError as error:
        raise HTTPException(
            status_code=422,
            detail="The corrected extraction failed TEAM-V1 validation.",
        ) from error

    # Keep server-assigned IDs stable across review revisions.
    if {skill.skill_id for skill in corrected.skills} != {
        skill.skill_id for skill in original.skills
    }:
        raise HTTPException(
            status_code=422,
            detail="Skill IDs cannot be changed during review.",
        )

    if {group.requirement_id for group in corrected.requirement_groups} != {
        group.requirement_id for group in original.requirement_groups
    }:
        raise HTTPException(
            status_code=422,
            detail="Requirement IDs cannot be changed during review.",
        )

    warnings = list(dict.fromkeys(original.warnings + corrected.warnings))
    if any(
        group.requirement_type == "unspecified"
        for group in corrected.requirement_groups
    ):
        warning = "One or more requirement groups are uncertain; confirm them."
        if warning not in warnings:
            warnings.append(warning)

    return corrected.model_copy(
        update={
            "revision": original.revision + 1,
            "review_status": "reviewed",
            "extraction_method": original.extraction_method,
            "warnings": warnings,
        }
    )