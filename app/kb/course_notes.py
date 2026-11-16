"""
Student-facing course notes and code resolution.

* Notes (data/seed/kb/course_note.csv) record where the official curriculum is inconsistent: a prerequisite named
  after no course, conflicting credits / codes / names. The app keeps the value the team chose and shows the note
  wherever the course appears, so nothing is silently "fixed".
* Course codes are NOT unique: the Metallurgy curriculum prints ML4L001-ML4L003 for both a Sem VII core course and
  an elective. Courses are keyed by an internal id (course.csv `course_id`, e.g. ML4L001_CORE / ML4L001_ELEC);
  a printed code is resolved with `resolve()`, which can return several courses.
"""
import csv
import os
from typing import Dict, List, Optional

CODE_CLASH_WARNING = "The official curriculum uses this code for two different courses. Please confirm with the department."
_SEED_KB = os.path.join("data", "seed", "kb")


class CourseNotes:
    def __init__(self, seed_dir: str = _SEED_KB):
        self.seed_dir = seed_dir
        self.reload()

    def _rows(self, name: str) -> List[Dict[str, str]]:
        path = os.path.join(self.seed_dir, name)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def reload(self) -> None:
        self.courses: Dict[str, Dict[str, str]] = {r["course_id"]: r for r in self._rows("course.csv")}
        self.notes: Dict[str, List[Dict[str, str]]] = {}
        for r in self._rows("course_note.csv"):
            self.notes.setdefault(r["course_id"], []).append(
                {"note_id": r["note_id"], "type": r["note_type"], "text": r["note_text"], "source_id": r.get("source_id")})
        # a course flagged code_conflict always carries the warning, even if a note row were missing
        for cid, c in self.courses.items():
            if str(c.get("code_conflict", "")).strip().lower() == "true":
                lst = self.notes.setdefault(cid, [])
                if not any(n["type"] == "code_conflict" for n in lst):
                    lst.insert(0, {"note_id": f"AUTO_{cid}_CLASH", "type": "code_conflict", "text": CODE_CLASH_WARNING,
                                   "source_id": c.get("source_id")})
        self.aliases: Dict[str, str] = {r["alias_name"].strip().lower(): r["target_course_id"] for r in self._rows("course_alias.csv")}

    # ------------------------------------------------------------------ lookups
    def notes_for(self, course_id: Optional[str]) -> List[Dict[str, str]]:
        return list(self.notes.get(course_id or "", []))

    def has_code_conflict(self, course_id: Optional[str]) -> bool:
        return any(n["type"] == "code_conflict" for n in self.notes.get(course_id or "", []))

    def display_code(self, course_id: Optional[str]) -> Optional[str]:
        c = self.courses.get(course_id or "")
        return (c.get("display_code") or c.get("course_code") or course_id) if c else course_id

    def resolve(self, code_or_id: str) -> List[str]:
        """
        Internal course ids for what a student typed: an internal id, a printed code (several courses can share one),
        or a known alias (another name or code the official sources use). Empty list when nothing matches.
        """
        key = (code_or_id or "").strip()
        if not key:
            return []
        if key in self.courses:
            return [key]
        upper = key.upper()
        matches = sorted(cid for cid, c in self.courses.items()
                         if upper in ((c.get("course_code") or "").upper(), (c.get("display_code") or "").upper()))
        if matches:
            return matches
        low = key.lower()
        for alias, target in self.aliases.items():
            if alias == low or alias.split(" (")[0] == low:
                return [target]
        return []

    def describe(self, course_id: str) -> str:
        c = self.courses.get(course_id, {})
        return f"{self.display_code(course_id)} {c.get('title', '')}".strip()


course_notes = CourseNotes()
