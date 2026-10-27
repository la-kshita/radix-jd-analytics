from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = PROJECT_ROOT / "samples"


def read_with_reader(filename: str, content: bytes) -> str:
    try:
        from backend.reader import read_document
    except ModuleNotFoundError as error:
        if error.name == "backend.reader":
            pytest.fail("backend.reader.read_document has not been implemented yet")
        raise
    except ImportError as error:
        if "read_document" in str(error):
            pytest.fail("backend.reader.read_document has not been implemented yet")
        raise

    return read_document(filename, content)


@pytest.mark.parametrize("extension", [".pdf", ".docx"])
def test_reads_jd_a_from_pdf_and_docx(extension: str) -> None:
    path = SAMPLES_DIR / f"jd_a{extension}"
    assert path.is_file(), f"Fixture is missing: {path}"

    text = read_with_reader(path.name, path.read_bytes())

    assert "Required: Python" in text
    assert "Preferred: SQL" in text


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("jd_a.txt", b"Required: Python"),
        ("jd_a.pdf", b"This is not a PDF"),
        ("jd_a.docx", b"This is not a DOCX file"),
    ],
)
def test_rejects_unsupported_or_corrupt_files(
    filename: str, content: bytes
) -> None:
    with pytest.raises(ValueError) as error:
        read_with_reader(filename, content)

    assert str(error.value).strip()


def test_rejects_files_over_10_megabytes() -> None:
    oversized_pdf = b"%PDF-1.7\n" + (b"x" * (10 * 1024 * 1024))

    with pytest.raises(ValueError) as error:
        read_with_reader("large.pdf", oversized_pdf)

    assert str(error.value).strip()


def test_rejects_docx_with_no_readable_text() -> None:
    empty_docx = BytesIO()
    Document().save(empty_docx)

    with pytest.raises(ValueError) as error:
        read_with_reader("empty.docx", empty_docx.getvalue())

    assert str(error.value).strip()

def get_models():
    from backend import models

    required = ("Skill", "Requirement", "Extraction")
    missing = [name for name in required if not hasattr(models, name)]

    if missing:
        pytest.fail(f"Missing model classes: {', '.join(missing)}")

    return models


def test_skill_accepts_a_valid_document_claim() -> None:
    models = get_models()

    skill = models.Skill(
        skill_id="jd-python",
        skill_name="Python",
        category_code="COD",
        evidence="Required: Python",
        confidence="medium",
        source_type="document",
        source_id="jd-1",
        source_page=None,
        claim_status="claimed",
    )

    assert skill.skill_name == "Python"
    assert skill.category_code == "COD"


def test_skill_rejects_an_unknown_category() -> None:
    models = get_models()

    with pytest.raises(ValidationError):
        models.Skill(
            skill_id="jd-python",
            skill_name="Python",
            category_code="PROGRAMMING",
            evidence="Required: Python",
            confidence="medium",
            source_type="document",
            source_id="jd-1",
            source_page=None,
            claim_status="claimed",
        )


def test_skill_rejects_unknown_fields() -> None:
    models = get_models()

    with pytest.raises(ValidationError):
        models.Skill(
            skill_id="jd-python",
            skill_name="Python",
            category_code="COD",
            evidence="Required: Python",
            confidence="medium",
            source_type="document",
            source_id="jd-1",
            source_page=None,
            claim_status="claimed",
            unexpected_field="not in TEAM-V1",
        )