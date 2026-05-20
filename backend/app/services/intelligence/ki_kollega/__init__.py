"""
KI Kollega - Intelligent AI Assistant for BEFS

This module provides the core AI assistant functionality including:
- Context-aware query processing
- Hybrid retrieval (semantic + structured)
- Natural language response generation
"""

from .service import KIKollegaService, ki_kollega_service

__all__ = ["KIKollegaService", "ki_kollega_service"]
