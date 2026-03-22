"""Base adapter interface. Every memory system implements this."""
from typing import List
from abc import ABC, abstractmethod


class MemoryAdapter(ABC):
    """Universal interface for testing any memory system.
    
    Two operations:
    1. ingest(message) — feed information in however the system naturally accepts it
    2. search(query) — ask a question, get text results back
    """
    
    name: str = "base"
    
    @abstractmethod
    def ingest(self, message: str, timestamp: str = None) -> dict:
        """Feed a message into the system the way a real user would.
        
        Args:
            message: Natural language message containing facts.
            timestamp: ISO timestamp of when this message was "said".
        
        Returns:
            dict with at least {"ok": bool}
        """
        pass
    
    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """Query the system for information.
        
        Returns:
            List of dicts, each with 'text' (full content, never truncated).
            Optionally 'score' and 'file_path'.
        """
        pass
    
    def health(self) -> bool:
        """Is the system ready?"""
        return True
    
    def stats(self) -> dict:
        """Return system stats (files, chunks, etc)."""
        return {}
    
    def reset(self) -> None:
        """Clear all data. Called before seeding a new test."""
        pass
