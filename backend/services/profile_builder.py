"""Build profile.json from resume and LinkedIn uploads."""

import csv
import json
import re
import tempfile
import zipfile
from pathlib import Path

import requests

from config import BACKEND_ROOT, OLLAMA_BASE_URL, OLLAMA_MODEL

PROFILE_KEYS = {
    "name", "current_role", "consulting", "experience_years", "target_roles",
    "target_market", "strong_areas", "needs_depth", "experience_highlights",
    "interview_styles_to_prepare", "study_style",
}

MAX_FILE_BYTES = 15 * 1024 * 1024  # 15 MB per file
MAX_TOTAL_BYTES = 50 * 1024 * 1024  # 50 MB total


def extract_text_from_pdf(data: bytes) -> str:
    """Extract text from PDF bytes."""
    from pypdf import PdfReader
    import io
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(data: bytes) -> str:
    """Extract text from DOCX bytes."""
    import io
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_from_txt(data: bytes) -> str:
    """Decode plain text."""
    return data.decode("utf-8", errors="replace")


def extract_text_from_linkedin_zip(data: bytes) -> str:
    """Extract and concatenate text from LinkedIn export ZIP (CSV/HTML)."""
    parts = []
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "linkedin.zip"
        path.write_bytes(data)
        with zipfile.ZipFile(path, "r") as zf:
            for name in zf.namelist():
                if name.startswith("__MACOSX") or "/." in name:
                    continue
                lower = name.lower()
                if not (lower.endswith(".csv") or lower.endswith(".html") or lower.endswith(".htm")):
                    continue
                try:
                    raw = zf.read(name)
                    text = raw.decode("utf-8", errors="replace")
                    if lower.endswith(".csv"):
                        parts.append(f"--- {name} ---\n" + _csv_to_text(text))
                    else:
                        parts.append(f"--- {name} ---\n" + _html_to_text(text))
                except Exception:
                    continue
    return "\n\n".join(parts) if parts else ""


def _csv_to_text(raw: str) -> str:
    """Convert CSV content to readable text."""
    lines = []
    try:
        for row in csv.reader(raw.splitlines()):
            lines.append(" | ".join(row))
    except Exception:
        lines = [raw[:50000]]
    return "\n".join(lines)


def _html_to_text(html: str) -> str:
    """Strip HTML tags for plain text."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:50000]


def _extract_resume(data: bytes, filename: str) -> str:
    """Dispatch resume extraction by extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(data)
    if lower.endswith(".docx"):
        return extract_text_from_docx(data)
    if lower.endswith(".txt"):
        return extract_text_from_txt(data)
    raise ValueError(f"Unsupported resume type: {filename}")


def _call_ollama_for_profile(combined: str) -> dict:
    """Call Ollama to fill profile schema from combined resume + LinkedIn text."""
    schema_desc = json.dumps({
        "name": "string",
        "current_role": "string",
        "consulting": "string",
        "experience_years": "number",
        "target_roles": "array of strings",
        "target_market": "string",
        "strong_areas": "array of strings",
        "needs_depth": "array of strings",
        "experience_highlights": "array of strings",
        "interview_styles_to_prepare": "array of strings",
        "study_style": "string",
    }, indent=2)

    prompt = f"""From the following resume(s) and LinkedIn export text, extract and fill a JSON object with exactly these keys. Output only valid JSON, no markdown or explanation.
Schema:
{schema_desc}

Rules:
- experience_years must be a number (integer).
- target_roles, strong_areas, needs_depth, experience_highlights, interview_styles_to_prepare must be arrays of strings.
- Infer study_style from tone or preferences if not stated (e.g. "Conversational, example-driven").
- Be specific; use the person's actual roles, companies, and skills.

Input text:
{combined[:60000]}"""

    url = f"{OLLAMA_BASE_URL}/api/generate"
    r = requests.post(
        url,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    response_text = r.json().get("response", "").strip()

    # Allow JSON inside markdown code block
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
    if match:
        response_text = match.group(1).strip()
    # Find first { ... }
    start = response_text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(response_text)):
            if response_text[i] == "{":
                depth += 1
            elif response_text[i] == "}":
                depth -= 1
                if depth == 0:
                    response_text = response_text[start : i + 1]
                    break

    obj = json.loads(response_text)
    # Normalize to schema
    result = {}
    for key in PROFILE_KEYS:
        val = obj.get(key)
        if key == "experience_years":
            result[key] = int(val) if isinstance(val, (int, float)) else 0
        elif key in ("target_roles", "strong_areas", "needs_depth", "experience_highlights", "interview_styles_to_prepare"):
            result[key] = list(val) if isinstance(val, list) else [str(val)] if val else []
        else:
            result[key] = str(val) if val is not None else ""
    return result


def build_profile_from_uploads(
    resume_files: list[tuple[str, bytes]],
    linkedin_zip_bytes: bytes | None,
) -> dict:
    """Build profile dict from resume file list and optional LinkedIn ZIP. Writes profile.json."""
    resume_texts = []
    for filename, data in resume_files:
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f"File too large: {filename}")
        text = _extract_resume(data, filename)
        resume_texts.append(f"--- Resume ({filename}) ---\n{text}")

    linkedin_text = ""
    if linkedin_zip_bytes:
        if len(linkedin_zip_bytes) > MAX_FILE_BYTES:
            raise ValueError("LinkedIn ZIP too large")
        linkedin_text = extract_text_from_linkedin_zip(linkedin_zip_bytes)

    combined = "Resumes:\n\n" + "\n\n".join(resume_texts)
    if linkedin_text:
        combined += "\n\nLinkedIn:\n\n" + linkedin_text

    if not combined.strip() or combined.strip() == "Resumes:":
        raise ValueError("No extractable text from uploads")

    profile = _call_ollama_for_profile(combined)
    path = BACKEND_ROOT / "profile.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
    return profile
