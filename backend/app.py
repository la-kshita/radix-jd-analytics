from typing import Annotated

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.extractor import extract_document
from backend.models import Extraction
from backend.reader import read_document
from backend.review import review_extraction


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

# In-memory private storage for this local build. Restarting the backend clears it.
_EXTRACTIONS_BY_ID: dict[str, Extraction] = {}


_ERROR_CODES = {
    404: "NOT_FOUND",
    409: "STALE_REVISION",
    413: "FILE_TOO_LARGE",
    415: "UNSUPPORTED_TYPE",
    422: "INVALID_INPUT",
    502: "INVALID_PROVIDER_OUTPUT",
    503: "SERVICE_UNAVAILABLE",
}


@app.exception_handler(HTTPException)
async def handle_http_exception(
    request: Request,
    error: HTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": _ERROR_CODES.get(error.status_code, "REQUEST_FAILED"),
                "message": str(error.detail),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_INPUT",
                "message": "The request fields or content are invalid.",
            }
        },
    )


class JDTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=15, max_length=100_000)
    source_file: str = Field(min_length=1)
    hosted_consent: bool = False

    @field_validator("source_file")
    @classmethod
    def source_file_must_be_txt_basename(cls, value: str) -> str:
        if "/" in value or "\\" in value or value in {".", ".."}:
            raise ValueError("source_file must be a filename, not a path")
        if not value.lower().endswith(".txt"):
            raise ValueError("source_file must end in .txt")
        return value


@app.get("/api/team/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _extract_and_store(
    source_file: str,
    source_text: str,
    hosted_consent: bool,
) -> Extraction:
    extraction = extract_document(
        source_type="jd",
        source_file=source_file,
        source_text=source_text,
        consent=hosted_consent,
    )
    _EXTRACTIONS_BY_ID[extraction.id] = extraction
    return extraction


@app.post(
    "/api/team/v1/jd/extract",
    response_model=Extraction,
)
def extract_jd_upload(
    file: Annotated[UploadFile, File()],
    hosted_consent: Annotated[bool, Form()] = False,
) -> Extraction:
    raw_filename = file.filename or ""
    source_file = raw_filename.replace("\\", "/").rsplit("/", 1)[-1]

    if not source_file:
        raise HTTPException(status_code=422, detail="A filename is required.")

    try:
        content = file.file.read()
        source_text = read_document(source_file, content)
    except ValueError as error:
        message = str(error)
        if "Only PDF and DOCX files are supported" in message:
            status_code = 415
        elif "10 MB limit" in message:
            status_code = 413
        else:
            status_code = 422
        raise HTTPException(status_code=status_code, detail=message) from error
    except OSError as error:
        raise HTTPException(
            status_code=503,
            detail="The uploaded document could not be read.",
        ) from error

    return _extract_and_store(source_file, source_text, hosted_consent)


@app.post(
    "/api/team/v1/jd/extract-text",
    response_model=Extraction,
)
def extract_jd_text(request: JDTextRequest) -> Extraction:
    return _extract_and_store(
        request.source_file,
        request.text,
        request.hosted_consent,
    )


@app.post(
    "/api/team/v1/jd/review",
    response_model=Extraction,
)
def review_jd(submitted: Extraction) -> Extraction:
    original = _EXTRACTIONS_BY_ID.get(submitted.id)
    if original is None:
        raise HTTPException(status_code=404, detail="Extraction was not found.")

    reviewed = review_extraction(original, submitted)
    _EXTRACTIONS_BY_ID[reviewed.id] = reviewed
    return reviewed