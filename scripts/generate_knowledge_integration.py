#!/usr/bin/env python3
"""Generate the knowledge integration schema for the AI Village Contribution Dashboard.

The script stitches together:
- Village goal periods (`data/village_goals.json`)
- Time Capsule document overlaps (`data/timecapsule_goal_mappings.json`)
- Timeline periods (`data/village_timeline.json`)
- Knowledge frameworks metadata (static definitions)

It emits `data/knowledge_integration.json` with bidirectional links between goals,
Time Capsule documents, timeline periods, and the shared knowledge frameworks.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
GOALS_PATH = DATA_DIR / "village_goals.json"
TIMECAPSULE_PATH = DATA_DIR / "timecapsule_goal_mappings.json"
TIMELINE_PATH = DATA_DIR / "village_timeline.json"
OUTPUT_PATH = DATA_DIR / "knowledge_integration.json"


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    with path.open() as f:
        return json.load(f)


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> Optional[Tuple[int, int]]:
    """Return the overlapping day range between [a_start, a_end] and [b_start, b_end]."""
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if start > end:
        return None
    return start, end


def normalize_timeline_periods(timeline: List[dict], goals: List[dict]) -> List[dict]:
    """Attach a stable id to each timeline period and map it back to a goal when possible."""
    periods: List[dict] = []
    for idx, period in enumerate(timeline):
        matched_goal = next(
            (
                g
                for g in goals
                if g.get("start_day") == period.get("start_day")
                and g.get("end_day") == period.get("end_day")
            ),
            None,
        )
        period_id = matched_goal["slug"] if matched_goal else f"timeline-{idx + 1}"
        periods.append(
            {
                "id": period_id,
                "label": period.get("goal"),
                "category": period.get("category"),
                "start_day": period.get("start_day"),
                "end_day": period.get("end_day"),
                "duration_days": period.get("duration_days")
                or (period.get("end_day") - period.get("start_day") + 1),
                "goal_slug": matched_goal["slug"] if matched_goal else None,
                "timecapsule_documents": [],
                "knowledge_frameworks": [],
            }
        )
    return periods


def build_goal_documents_map(timecapsule_docs: Iterable[dict]) -> Dict[str, List[dict]]:
    """Return goal_slug -> list of overlapping documents with overlap metadata."""
    goal_to_docs: Dict[str, List[dict]] = {}
    for doc_block in timecapsule_docs:
        doc_name = doc_block["document"]["name"]
        for overlap in doc_block.get("overlapping_goals", []):
            goal_to_docs.setdefault(overlap["goal_slug"], []).append(
                {
                    "document": doc_name,
                    "overlap_start_day": overlap["overlap_start_day"],
                    "overlap_end_day": overlap["overlap_end_day"],
                    "overlap_days": overlap["overlap_days"],
                    "goal_coverage_pct": overlap["goal_coverage_pct"],
                    "document_coverage_pct": overlap["document_coverage_pct"],
                }
            )
    return goal_to_docs


def build_timeline_document_links(periods: List[dict], documents: List[dict]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Return mappings between timeline ids and overlapping documents."""
    timeline_to_docs: Dict[str, List[str]] = {p["id"]: [] for p in periods}
    doc_to_timeline: Dict[str, List[str]] = {}

    for period in periods:
        for doc in documents:
            overlap_range = overlaps(period["start_day"], period["end_day"], doc["start_day"], doc["end_day"])
            if not overlap_range:
                continue
            timeline_to_docs[period["id"]].append(doc["name"])
            doc_to_timeline.setdefault(doc["name"], []).append(period["id"])

    # Sort for stable output
    for doc_list in timeline_to_docs.values():
        doc_list.sort()
    for period_list in doc_to_timeline.values():
        period_list.sort()

    return timeline_to_docs, doc_to_timeline


def knowledge_frameworks_metadata() -> List[dict]:
    """Static metadata for the shared knowledge frameworks."""
    return [
        {
            "id": "decision_frameworks",
            "title": "Decision Frameworks",
            "description": "Playbooks for selecting goals, sequencing work, and making tradeoffs.",
            "url": "decision_frameworks.md",
        },
        {
            "id": "institutional_memory",
            "title": "Institutional Memory",
            "description": "Persistent lessons learned, norms, and recurring patterns from past work.",
            "url": "institutional_memory.md",
        },
        {
            "id": "problem_solving_templates",
            "title": "Problem-Solving Templates",
            "description": "Reusable templates for experiments, incident response, and retrospectives.",
            "url": "problem_solving_templates.md",
        },
    ]


def build_payload() -> dict:
    goals = load_json(GOALS_PATH)
    timecapsule = load_json(TIMECAPSULE_PATH)
    timeline = load_json(TIMELINE_PATH).get("goals", [])

    frameworks = knowledge_frameworks_metadata()
    framework_ids = [fw["id"] for fw in frameworks]

    goal_to_docs = build_goal_documents_map(timecapsule.get("documents", []))

    timeline_periods = normalize_timeline_periods(timeline, goals)

    docs_payload: List[dict] = []
    doc_to_goals: Dict[str, List[str]] = {}
    for doc_block in timecapsule.get("documents", []):
        doc_info = doc_block["document"]
        name = doc_info["name"]
        doc_to_goals[name] = [g["goal_slug"] for g in doc_block.get("overlapping_goals", [])]
        docs_payload.append(
            {
                "name": name,
                "description": doc_info.get("description"),
                "author": doc_info.get("author"),
                "category": doc_info.get("category"),
                "start_day": doc_info.get("start_day"),
                "end_day": doc_info.get("end_day"),
                "duration_days": doc_info.get("duration_days"),
                "period": doc_info.get("period"),
                "link": doc_info.get("link"),
                "overlapping_goals": doc_block.get("overlapping_goals", []),
                "timeline_periods": [],
                "knowledge_frameworks": framework_ids,
            }
        )

    timeline_to_docs, doc_to_timeline = build_timeline_document_links(timeline_periods, docs_payload)
    for period in timeline_periods:
        period["timecapsule_documents"] = timeline_to_docs.get(period["id"], [])
        period["knowledge_frameworks"] = framework_ids

    for doc in docs_payload:
        doc["timeline_periods"] = doc_to_timeline.get(doc["name"], [])

    goals_payload: List[dict] = []
    slug_to_timeline_ids: Dict[str, Set[str]] = {}
    for period in timeline_periods:
        if period["goal_slug"]:
            slug_to_timeline_ids.setdefault(period["goal_slug"], set()).add(period["id"])

    for goal in goals:
        goals_payload.append(
            {
                "slug": goal["slug"],
                "title": goal.get("title"),
                "href": goal.get("href"),
                "start_day": goal.get("start_day"),
                "end_day": goal.get("end_day"),
                "duration_days": goal.get("duration_days") or (goal.get("end_day") - goal.get("start_day") + 1),
                "timecapsule_documents": sorted(goal_to_docs.get(goal["slug"], []), key=lambda d: (-d["overlap_days"], d["document"])),
                "timeline_periods": sorted(slug_to_timeline_ids.get(goal["slug"], set())),
                "knowledge_frameworks": framework_ids,
            }
        )

    frameworks_payload: List[dict] = []
    all_goal_slugs = sorted(g["slug"] for g in goals_payload)
    all_doc_names = sorted(doc["name"] for doc in docs_payload)
    all_timeline_ids = sorted(p["id"] for p in timeline_periods)
    for fw in frameworks:
        frameworks_payload.append(
            {
                **fw,
                "related_goals": all_goal_slugs,
                "related_documents": all_doc_names,
                "related_timeline_periods": all_timeline_ids,
            }
        )

    references = {
        "goal_to_documents": {goal["slug"]: [d["document"] for d in goal_to_docs.get(goal["slug"], [])] for goal in goals},
        "document_to_goals": doc_to_goals,
        "timeline_to_documents": timeline_to_docs,
        "document_to_timeline": doc_to_timeline,
        "knowledge_framework_to_entities": {
            fw["id"]: {
                "goals": all_goal_slugs,
                "documents": all_doc_names,
                "timeline_periods": all_timeline_ids,
            }
            for fw in frameworks
        },
    }

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "sources": {
            "village_goals": str(GOALS_PATH),
            "timecapsule_goal_mappings": str(TIMECAPSULE_PATH),
            "village_timeline": str(TIMELINE_PATH),
        },
        "goals": goals_payload,
        "timecapsule_documents": docs_payload,
        "timeline_periods": timeline_periods,
        "knowledge_frameworks": frameworks_payload,
        "references": references,
    }


def main():
    payload = build_payload()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote knowledge integration schema to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
