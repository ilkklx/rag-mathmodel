# -*- coding: utf-8 -*-
"""RAG-MathModel：数学建模知识检索底座（可移植版）。"""
from .guard import check as guard_check  # noqa: F401
from .retrieve import retrieve  # noqa: F401

__version__ = "1.0.0"
__all__ = ["retrieve", "guard_check", "__version__"]
