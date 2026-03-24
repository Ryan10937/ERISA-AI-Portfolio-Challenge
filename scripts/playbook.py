"""
Playbook Class
==============
Loads and indexes ERISA claim denial playbook from JSONL chunks. Provides tag-based lookup
and markdown document retrieval for playbook guidance on specific denial scenarios.
"""
from pathlib import Path
from typing import Dict, List, Any
import json

class Playbook:
    def __init__(self, jsonl_path: str, docs_root: str = "docs/playbook"):
        self.jsonl_path = Path(jsonl_path)
        self.docs_root = Path(docs_root)

        # --- Load & parse JSONL --------------------------------------------
        self.chunks: List[Dict[str, Any]] = []

        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue  # skip blank lines
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Malformed JSON on line {line_no} of {self.jsonl_path}"
                    ) from exc
                self.chunks.append(chunk)

        # Build quick look-ups
        self.by_id: Dict[str, Dict[str, Any]] = {c["chunk_id"]: c for c in self.chunks}
        self.tag_index: Dict[str, List[str]] = {}
        for c in self.chunks:
            for tag in c["tags"]:
                self.tag_index.setdefault(tag, []).append(c["chunk_id"])

    def get_chunks_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """Return the intersection of chunks that contain *all* supplied tags."""
        if not tags:
            return []

        # Start with the set for the first tag
        common = set(self.tag_index.get(tags[0], []))
        for t in tags[1:]:
            common &= set(self.tag_index.get(t, []))

        return [self.by_id[cid] for cid in common]

    def load_markdown_for_chunk(self, chunk: Dict[str, Any]) -> str:
        """
        The `doc_id` field points at the markdown file name *without* extension.
        e.g. `doc_id="medical_necessity.md"` → load `docs/playbook/medical_necessity.md`
        """
        doc_file = self.docs_root / f"{chunk['doc_id']}"
        if not doc_file.exists():
            return f"[ERROR: missing {doc_file}]"

        return doc_file.read_text(encoding="utf-8")

    def load_markdown_for_tags(self, tags: List[str]) -> Dict[str, str]:
        """Return a mapping of doc_id → file contents for all chunks matching the tags."""
        chunks = self.get_chunks_by_tags(tags)
        return {c["doc_id"]: self.load_markdown_for_chunk(c) for c in chunks}
