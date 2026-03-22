#!/usr/bin/env python3
"""
OpenClaw Native Memory Adapter for IRONMAN
Uses `openclaw memory search` CLI to query OC's built-in memory system.
"""
import subprocess
import json
import re
import time
from typing import List, Dict


class OCMemoryAdapter:
    """Adapter for OpenClaw's native memory search via CLI."""
    
    name = "OpenClaw Native (text-embedding-3-small)"
    
    def __init__(self, ssh_target: str = None):
        """
        Args:
            ssh_target: SSH target for remote execution (e.g. "user@10.0.0.1") for remote execution.
                       None for local execution.
        """
        self.ssh_target = ssh_target
        self.ssh_prefix = f"ssh -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no -o ConnectTimeout=5 {ssh_target}" if ssh_target else ""
    
    def _run(self, cmd: str, timeout: int = 30) -> str:
        """Run a command locally or via SSH."""
        if self.ssh_prefix:
            full_cmd = f'{self.ssh_prefix} "{cmd}"'
        else:
            full_cmd = cmd
        
        try:
            result = subprocess.run(
                full_cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            return str(e)
    
    def index(self, directory: str, **kwargs) -> dict:
        """OC indexes from its workspace/memory/ directory. Already done."""
        output = self._run("openclaw memory index --force", timeout=300)
        return {"output": output}
    
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """Search using openclaw memory search CLI."""
        # Escape quotes in query
        safe_query = query.replace('"', '\\"').replace("'", "\\'").replace('`', '\\`').replace('$', '\\$')
        
        cmd = f"openclaw memory search --max-results {max_results} --json '{safe_query}'"
        output = self._run(cmd, timeout=15)
        
        # Try to parse JSON output
        try:
            # Find JSON in output (might have warnings before it)
            json_match = re.search(r'[\[\{].*', output, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if isinstance(data, list):
                    return [{"text": r.get("text", r.get("snippet", "")), 
                             "score": r.get("score", 0),
                             "file_path": r.get("path", "")} for r in data]
                elif isinstance(data, dict) and "results" in data:
                    return [{"text": r.get("text", r.get("snippet", "")),
                             "score": r.get("score", 0),
                             "file_path": r.get("path", "")} for r in data["results"]]
        except json.JSONDecodeError:
            pass
        
        # Fallback: parse the text output format
        # Format: "0.375 memory/file.md:1-30\ncontent..."
        results = []
        blocks = re.split(r'\n(?=\d+\.\d+ )', output)
        for block in blocks:
            match = re.match(r'(\d+\.\d+)\s+(\S+):(\d+)-(\d+)\n(.*)', block, re.DOTALL)
            if match:
                score = float(match.group(1))
                path = match.group(2)
                text = match.group(5).strip()
                results.append({
                    "text": text,
                    "score": score,
                    "file_path": path,
                })
        
        return results[:max_results]
    
    def clear(self) -> None:
        """Can't easily clear OC's index without removing files."""
        pass
    
    def stats(self) -> dict:
        output = self._run("openclaw memory status")
        # Parse basic stats
        chunks = 0
        files = 0
        for line in output.split('\n'):
            m = re.search(r'(\d+)/(\d+) files.*?(\d+) chunks', line)
            if m:
                files = int(m.group(2))
                chunks = int(m.group(3))
        return {"files": files, "total_chunks": chunks}
    
    def health(self) -> bool:
        output = self._run("openclaw memory status")
        return "ready" in output.lower()
    
    def restart(self) -> None:
        pass  # No restart needed for CLI


if __name__ == "__main__":
    # Quick test
    adapter = OCMemoryAdapter(ssh_target="user@localhost")
    
    print("Health:", adapter.health())
    print("Stats:", adapter.stats())
    print()
    
    test_queries = [
        "Nexus Dynamics EIN number",
        "Who founded the company?",
        "Datadog API key",
        "What is the 401k match?",
    ]
    
    for q in test_queries:
        results = adapter.search(q, max_results=3)
        print(f"Q: {q}")
        for r in results:
            print(f"  {r['score']:.3f} | {r['text'][:80]}")
        print()
