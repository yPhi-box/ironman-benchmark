"""OpenClaw adapter — writes files to memory/, indexes via CLI, searches via CLI.

Same data format as HMS (daily markdown files).
Search uses openclaw memory search CLI.

IMPORTANT: Defaults to /tmp/ironman-oc-workspace to avoid touching your real data.
Set workspace= to override, but be careful with reset() — it deletes files.
"""
import os
import re
import time
import subprocess
import glob
from typing import List
from .base import MemoryAdapter


class OCAdapter(MemoryAdapter):
    """OpenClaw native memory via CLI. Run ON the OC machine."""
    name = "OpenClaw Native"
    
    def __init__(self, workspace: str = None, **kwargs):
        self.workspace = workspace or "/tmp/ironman-oc-workspace/memory"
    
    def ingest(self, message: str, timestamp: str = None) -> dict:
        """Write message to memory/*.md — same format as HMS adapter."""
        date = timestamp[:10] if timestamp else time.strftime("%Y-%m-%d")
        filepath = os.path.join(self.workspace, f"{date}.md")
        os.makedirs(self.workspace, exist_ok=True)
        
        with open(filepath, "a") as f:
            if timestamp:
                f.write(f"\n## {timestamp}\n")
            f.write(f"{message}\n\n")
        
        return {"ok": True, "file": filepath}
    
    def flush_index(self) -> dict:
        """Trigger OC memory reindex after all files are written."""
        r = subprocess.run("openclaw memory index --force",
                          shell=True, capture_output=True, text=True, timeout=300)
        return {"output": r.stdout[:200]}
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """Search via openclaw memory search CLI."""
        safe = query.replace("'", "'\\''")
        cmd = f"openclaw memory search --max-results {max_results} '{safe}'"
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            output = r.stdout + r.stderr
        except:
            return []
        
        if "No matches" in output:
            return []
        
        results = []
        blocks = re.split(r'\n(?=\d+\.\d+ )', output.strip())
        for block in blocks:
            m = re.match(r'(\d+\.\d+)\s+(\S+):(\d+)-(\d+)\n(.*)', block, re.DOTALL)
            if m:
                results.append({
                    "text": m.group(5).strip(),
                    "score": float(m.group(1)),
                    "file_path": m.group(2),
                })
        return results[:max_results]
    
    def health(self) -> bool:
        r = subprocess.run("openclaw memory status",
                          shell=True, capture_output=True, text=True, timeout=10)
        return "ready" in r.stdout.lower()
    
    def stats(self) -> dict:
        r = subprocess.run("openclaw memory status",
                          shell=True, capture_output=True, text=True, timeout=10)
        chunks = files = 0
        for line in r.stdout.split('\n'):
            m = re.search(r'(\d+)/(\d+) files.*?(\d+) chunks', line)
            if m:
                files = int(m.group(2))
                chunks = int(m.group(3))
        return {"files": files, "chunks": chunks}
    
    def reset(self) -> None:
        """Clear benchmark data. Only deletes from the configured workspace."""
        if "/tmp/" not in self.workspace and "ironman" not in self.workspace.lower():
            raise RuntimeError(
                f"SAFETY: reset() refused — workspace '{self.workspace}' doesn't look like a "
                f"benchmark directory. Set workspace to a /tmp/ path or include 'ironman' in the name."
            )
        for f in glob.glob(os.path.join(self.workspace, "*.md")):
            os.remove(f)
