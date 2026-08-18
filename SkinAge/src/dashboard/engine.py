"""
Shared analysis engine for the Streamlit dashboard.

Provides a singleton InferencePipeline (using trained model) with
DemoInferencePipeline fallback.
No API server needed - runs inference directly in the Streamlit process.
"""

from __future__ import annotations

import logging
from pathlib import Path
import streamlit as st

logger = logging.getLogger(__name__)


@st.cache_resource
def get_pipeline():
    """Return a cached inference pipeline singleton (Real Model or Demo fallback)."""
    # Check if real trained model checkpoint exists
    model_path = Path("outputs/models/best_model.pth")
    if not model_path.exists():
        model_path = Path(__file__).resolve().parents[2] / "outputs" / "models" / "best_model.pth"

    if model_path.exists():
        try:
            from src.api.inference import InferencePipeline
            logger.info("Initializing real trained InferencePipeline from %s...", model_path)
            return InferencePipeline(device="cuda" if st.session_state.get("use_cuda", True) else "cpu")
        except Exception as exc:
            logger.warning("Failed to load real InferencePipeline (%s); falling back to DemoPipeline.", exc)

    from src.api.demo import DemoInferencePipeline
    return DemoInferencePipeline()


def analyze(image_bytes: bytes, age: int | None = None, include_heatmaps: bool = True) -> dict:
    """Run analysis and return result as a plain dict (matching API schema)."""
    pipeline = get_pipeline()
    response = pipeline.run(image_bytes, age=age, include_heatmaps=include_heatmaps)
    return response.model_dump()

