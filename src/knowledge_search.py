from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"


def _safe_json_load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


@lru_cache(maxsize=8)
def load_json_file(filename: str) -> dict:
    """Load one JSON knowledge file from the project knowledge directory."""
    return _safe_json_load(KNOWLEDGE_DIR / filename)


def clear_knowledge_cache() -> None:
    load_json_file.cache_clear()


def get_profile() -> dict:
    return load_json_file("profile.json")


def get_projects() -> list[dict]:
    data = load_json_file("projects.json")
    projects = data.get("projects", [])
    return projects if isinstance(projects, list) else []


def normalize_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9+#.-]+", str(text).lower())
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "what", "which",
        "how", "do", "does", "about", "and", "or", "of", "to", "in",
        "for", "with", "my", "his", "him", "this", "that", "on", "it",
    }
    return {word for word in words if word not in stop_words}


def get_profile_context() -> str:
    profile = get_profile()
    if not profile:
        return "Profile knowledge is currently unavailable."
    return json.dumps(profile, indent=2, default=str)


def search_projects(question: str, top_k: int = 3) -> list[dict]:
    projects = get_projects()
    if not projects:
        return []

    question_words = normalize_words(question)
    question_lower = question.lower()
    results: list[dict] = []

    aliases = {
        "retail": "retail",
        "lakehouse": "lakehouse",
        "data quality": "data quality",
        "aiops": "aiops",
        "serverless": "serverless",
        "finops": "finops",
    }

    for project in projects:
        name = str(project.get("name", "Project"))
        project_text = json.dumps(project, default=str)
        name_words = normalize_words(name)
        project_words = normalize_words(project_text)

        score = len(question_words & name_words) * 5 + len(question_words & project_words)
        name_lower = name.lower()

        for query_alias, name_alias in aliases.items():
            if query_alias in question_lower and name_alias in name_lower:
                score += 10

        if score > 0:
            results.append({"name": name, "score": score, "project": project})

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[: max(1, int(top_k))]


def get_project_context(question: str, top_k: int = 3) -> str:
    results = search_projects(question, top_k=top_k)
    if not results:
        return "No directly matching projects were found."
    return "\n\n".join(
        json.dumps(result["project"], indent=2, default=str)
        for result in results
    )


def build_knowledge_context(
    question: str,
    include_profile: bool = True,
    include_projects: bool = True,
) -> str:
    parts: list[str] = []
    if include_profile:
        parts.append("PROFILE:\n" + get_profile_context())
    if include_projects:
        parts.append("PROJECTS:\n" + get_project_context(question))
    return "\n\n".join(parts) if parts else "No portfolio context requested."


def get_knowledge_status() -> dict:
    profile_path = KNOWLEDGE_DIR / "profile.json"
    projects_path = KNOWLEDGE_DIR / "projects.json"
    profile = get_profile()
    projects = get_projects()

    return {
        "project_root": str(PROJECT_ROOT),
        "knowledge_directory": str(KNOWLEDGE_DIR),
        "profile_path": str(profile_path),
        "profile_exists": profile_path.exists(),
        "profile_loaded": bool(profile),
        "projects_path": str(projects_path),
        "projects_exists": projects_path.exists(),
        "projects_loaded": len(projects),
    }
