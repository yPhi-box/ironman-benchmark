"""HMS adapter — talks to HMS via HTTP API.

Ingest: writes message to a file, then calls /index.
        HMS chunks, embeds, and extracts entities naturally.
Search: POST /search — returns chunks with scores.

IMPORTANT: Defaults to /tmp/ironman-hms-data to avoid touching your real workspace.
"""
import os
import time
import requests
from typing import List
from .base import MemoryAdapter


class HMSAdapter(MemoryAdapter):
    name = "HMS v2.4 (all-MiniLM-L6-v2 + cross-encoder, local)"
    
    def __init__(self, url: str = "http://localhost:8765",
                 workspace: str = None):
        self.url = url.rstrip("/")
        self.workspace = workspace or "/tmp/ironman-hms-data"
        self.session = requests.Session()
    
    def ingest(self, message: str, timestamp: str = None) -> dict:
        """Write message to a daily file, then index.
        
        HMS indexes files from a directory. We write messages to daily
        markdown files (same format OC uses), then tell HMS to index.
        """
        if timestamp:
            date = timestamp[:10]
        else:
            date = time.strftime("%Y-%m-%d")
        
        filepath = os.path.join(self.workspace, f"{date}.md")
        os.makedirs(self.workspace, exist_ok=True)
        with open(filepath, "a") as f:
            if timestamp:
                f.write(f"\n## {timestamp}\n")
            f.write(f"{message}\n\n")
        
        return {"ok": True, "file": filepath}
    
    def flush_index(self) -> dict:
        """Call after all ingest() calls to trigger indexing."""
        try:
            r = self.session.post(f"{self.url}/index", json={
                "directory": self.workspace,
                "pattern": "**/*.md",
                "force": True,
            }, timeout=300)
            return r.json()
        except Exception as e:
            return {"error": str(e)}
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """Search HMS. Returns full chunk text."""
        try:
            r = self.session.post(f"{self.url}/search", json={
                "query": query,
                "max_results": max_results,
            }, timeout=30)
            if r.status_code == 200:
                return r.json().get("results", [])
            return []
        except:
            return []
    
    def health(self) -> bool:
        try:
            r = self.session.get(f"{self.url}/health", timeout=5)
            return r.status_code == 200
        except:
            return False
    
    def stats(self) -> dict:
        try:
            r = self.session.get(f"{self.url}/stats", timeout=10)
            return r.json()
        except:
            return {}
    
    def reset(self) -> None:
        """Clear benchmark data. Only deletes from the configured workspace."""
        import shutil
        
        if "/tmp/" not in self.workspace and "ironman" not in self.workspace.lower():
            raise RuntimeError(
                f"SAFETY: reset() refused — workspace '{self.workspace}' doesn't look like a "
                f"benchmark directory. Set workspace to a /tmp/ path or include 'ironman' in the name."
            )
        
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)
        os.makedirs(self.workspace, exist_ok=True)
        
        # Re-index empty directory
        self.flush_index()
