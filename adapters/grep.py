"""Grep baseline adapter — sets the floor.

Ingest: writes messages to daily files (same as HMS).
Search: keyword matching across all files. Returns full file content.
"""
import os
import time
from pathlib import Path
from typing import List
from .base import MemoryAdapter


class GrepAdapter(MemoryAdapter):
    name = "grep (baseline)"
    
    def __init__(self, workspace: str = "/tmp/ironman-grep-data"):
        self.workspace = workspace
        self.files = {}
    
    def ingest(self, message: str, timestamp: str = None) -> dict:
        """Write to daily files."""
        date = timestamp[:10] if timestamp else time.strftime("%Y-%m-%d")
        filepath = os.path.join(self.workspace, f"{date}.md")
        os.makedirs(self.workspace, exist_ok=True)
        with open(filepath, "a") as f:
            if timestamp:
                f.write(f"\n## {timestamp}\n")
            f.write(f"{message}\n\n")
        return {"ok": True}
    
    def _load_files(self):
        """Load all files for searching."""
        self.files = {}
        for p in Path(self.workspace).rglob("*.md"):
            self.files[str(p)] = p.read_text(errors="ignore")
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """Keyword search. Returns full file content."""
        if not self.files:
            self._load_files()
        
        if not query.strip():
            return []
        
        words = query.lower().split()
        results = []
        for path, text in self.files.items():
            text_lower = text.lower()
            score = sum(1 for w in words if w in text_lower) / max(len(words), 1)
            if score > 0:
                results.append({
                    "text": text,  # Full file content
                    "score": score,
                    "file_path": path,
                })
        
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:max_results]
    
    def health(self) -> bool:
        return True
    
    def stats(self) -> dict:
        self._load_files()
        return {"files": len(self.files)}
    
    def reset(self) -> None:
        import shutil
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)
        os.makedirs(self.workspace, exist_ok=True)
        self.files = {}
