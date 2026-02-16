#!/usr/bin/env python3
"""Map Time Capsule history documents to Village goals and compute coverage stats."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parent.parent
GOALS_PATH = ROOT / "data" / "village_goals.json"
README_PATH = ROOT / ".." / "village-time-capsule" / "content" / "history" / "README.md"
OUTPUT_MAPPINGS_PATH = ROOT / "data" / "timecapsule_goal_mappings.json"
OUTPUT_COVERAGE_PATH = ROOT / "data" / "goal_coverage_stats.json"


@dataclass
class Goal:
    slug: str
    title: str
    start_day: int
    end_day: int

    @property
    def duration(self) -> int:
        return self.end_day - self.start_day + 1


@dataclass
class Document:
    name: str
    description: str
    period_text: str
    author: str
    start_day: int
    end_day: int
    link: Optional[str] = None
    category: Optional[str] = None

    @property
    def duration(self) -> int:
        return self.end_day - self.start_day + 1


def load_goals() -> List[Goal]:
    with GOALS_PATH.open() as f:
        raw = json.load(f)
    return [
        Goal(
            slug=item["slug"],
            title=item["title"],
            start_day=int(item["start_day"]),
            end_day=int(item["end_day"]),
        )
        for item in raw
    ]


def split_row(line: str) -> List[str]:
    parts = [part.strip() for part in line.strip().strip("|").split("|")]
    return [p for p in parts]


def is_separator_row(cells: Sequence[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_markdown_link(cell: str) -> Tuple[str, Optional[str]]:
    match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", cell)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return cell.strip(), None


def parse_day_range(text: str) -> Optional[Tuple[int, int]]:
    match = re.search(r"days?\s*(\d+)\s*(?:-\s*(\d+))?", text, re.IGNORECASE)
    if not match:
        return None
    start = int(match.group(1))
    end = int(match.group(2) or match.group(1))
    if start > end:
        start, end = end, start
    return start, end


def parse_document_tables(readme_text: str) -> List[Document]:
    documents: List[Document] = []
    lines = readme_text.splitlines()
    current_heading: Optional[str] = None
    i = 0

    while i < len(lines):
        line = lines[i]
        heading_match = re.match(r"^(#{2,6})\s+(.*)", line)
        if heading_match:
            current_heading = heading_match.group(2).strip()
            i += 1
            continue

        if line.strip().startswith("|"):
            table_lines: List[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            documents.extend(parse_single_table(table_lines, current_heading))
            continue

        i += 1

    return documents


def parse_single_table(table_lines: Sequence[str], heading: Optional[str]) -> List[Document]:
    if len(table_lines) < 2:
        return []

    header_cells = split_row(table_lines[0])
    separator_cells = split_row(table_lines[1])
    if not is_separator_row(separator_cells):
        return []

    columns = [c.lower() for c in header_cells]
    try:
        doc_idx = columns.index("document")
        author_idx = columns.index("author")
    except ValueError:
        return []

    desc_idx = None
    period_idx = None
    for idx, col in enumerate(columns):
        if "description" in col:
            desc_idx = idx
        if "period" in col or "example" in col:
            period_idx = idx

    if desc_idx is None or period_idx is None:
        return []

    parsed: List[Document] = []
    for row_line in table_lines[2:]:
        cells = split_row(row_line)
        if len(cells) < len(columns):
            continue
        if is_separator_row(cells):
            continue

        doc_cell = cells[doc_idx]
        desc_cell = cells[desc_idx]
        period_cell = cells[period_idx]
        author_cell = cells[author_idx]

        name, link = parse_markdown_link(doc_cell)
        day_range = parse_day_range(period_cell)
        if not day_range:
            continue

        start_day, end_day = day_range
        parsed.append(
            Document(
                name=name,
                description=desc_cell,
                period_text=period_cell,
                author=author_cell,
                start_day=start_day,
                end_day=end_day,
                link=link,
                category=heading,
            )
        )

    return parsed


def compute_overlaps(documents: Iterable[Document], goals: Iterable[Goal]):
    doc_mappings = []
    goals_list = list(goals)

    for doc in documents:
        overlaps = []
        for goal in goals_list:
            if doc.start_day > goal.end_day or doc.end_day < goal.start_day:
                continue
            overlap_start = max(doc.start_day, goal.start_day)
            overlap_end = min(doc.end_day, goal.end_day)
            overlap_days = overlap_end - overlap_start + 1
            goal_pct = round((overlap_days / goal.duration) * 100, 2)
            doc_pct = round((overlap_days / doc.duration) * 100, 2)
            overlaps.append(
                {
                    "goal_slug": goal.slug,
                    "goal_title": goal.title,
                    "goal_start_day": goal.start_day,
                    "goal_end_day": goal.end_day,
                    "overlap_start_day": overlap_start,
                    "overlap_end_day": overlap_end,
                    "overlap_days": overlap_days,
                    "goal_coverage_pct": goal_pct,
                    "document_coverage_pct": doc_pct,
                }
            )

        doc_mappings.append(
            {
                "document": {
                    "name": doc.name,
                    "description": doc.description,
                    "author": doc.author,
                    "period": doc.period_text,
                    "start_day": doc.start_day,
                    "end_day": doc.end_day,
                    "duration_days": doc.duration,
                    "category": doc.category,
                    "link": doc.link,
                },
                "overlapping_goals": sorted(
                    overlaps, key=lambda o: (-o["overlap_days"], o["goal_start_day"])
                ),
            }
        )

    return doc_mappings


def compute_goal_coverage(documents: Iterable[Document], goals: Iterable[Goal]):
    goals_list = list(goals)
    docs_list = list(documents)
    stats = []

    for goal in goals_list:
        covered_days = set()
        covering_docs = []

        for doc in docs_list:
            if doc.start_day > goal.end_day or doc.end_day < goal.start_day:
                continue
            overlap_start = max(doc.start_day, goal.start_day)
            overlap_end = min(doc.end_day, goal.end_day)
            overlap_days = overlap_end - overlap_start + 1
            covered_days.update(range(overlap_start, overlap_end + 1))
            covering_docs.append(
                {
                    "document": doc.name,
                    "link": doc.link,
                    "overlap_start_day": overlap_start,
                    "overlap_end_day": overlap_end,
                    "overlap_days": overlap_days,
                }
            )

        coverage_pct = round((len(covered_days) / goal.duration) * 100, 2) if goal.duration else 0.0
        stats.append(
            {
                "goal_slug": goal.slug,
                "goal_title": goal.title,
                "start_day": goal.start_day,
                "end_day": goal.end_day,
                "duration_days": goal.duration,
                "covered_days": len(covered_days),
                "coverage_pct": coverage_pct,
                "covering_documents": sorted(
                    covering_docs, key=lambda d: (-d["overlap_days"], d["overlap_start_day"])
                ),
            }
        )

    return stats


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f, indent=2)


def summarize_coverage(stats: Sequence[dict]) -> str:
    if not stats:
        return "No goals available."

    sorted_by_pct = sorted(stats, key=lambda g: g["coverage_pct"], reverse=True)
    best = sorted_by_pct[:3]
    worst = sorted(stats, key=lambda g: g["coverage_pct"])[:3]

    def fmt(items: Sequence[dict]) -> str:
        return "; ".join(
            f"{item['goal_title']} (Days {item['start_day']}-{item['end_day']}, "
            f"{item['coverage_pct']}% over {item['covered_days']} days)"
            for item in items
        )

    goals_with_docs = sum(1 for item in stats if item["covered_days"] > 0)
    summary_lines = [
        f"Goals with coverage: {goals_with_docs}/{len(stats)}",
        f"Most covered: {fmt(best)}",
        f"Least covered: {fmt(worst)}",
    ]
    return "\n".join(summary_lines)


def main():
    if not GOALS_PATH.exists():
        raise SystemExit(f"Missing village goals file: {GOALS_PATH}")
    if not README_PATH.exists():
        raise SystemExit(f"Missing Time Capsule README: {README_PATH}")

    goals = load_goals()
    readme_text = README_PATH.read_text(encoding="utf-8")
    documents = parse_document_tables(readme_text)

    doc_mappings = compute_overlaps(documents, goals)
    goal_coverage = compute_goal_coverage(documents, goals)

    generated_at = datetime.utcnow().isoformat() + "Z"
    write_json(
        OUTPUT_MAPPINGS_PATH,
        {"generated_at": generated_at, "documents": doc_mappings},
    )
    write_json(
        OUTPUT_COVERAGE_PATH,
        {"generated_at": generated_at, "goals": goal_coverage},
    )

    print(f"Documents parsed: {len(documents)}")
    print(f"Goals loaded: {len(goals)}")
    print("Coverage summary:")
    print(summarize_coverage(goal_coverage))


if __name__ == "__main__":
    main()
