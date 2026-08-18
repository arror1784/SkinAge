"""
Model weight downloader for SkinAge.

Downloads the trained model weights (best_model.pth) to outputs/models/
if not already present locally.
"""

from __future__ import annotations

import logging
import os
import sys
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[1]  # SkinAge/
_MODELS_DIR = _PROJECT_ROOT / "outputs" / "models"
_WEIGHTS_FILE = _MODELS_DIR / "best_model.pth"

# Primary & fallback download URLs (GitHub Release / Mirror)
_DEFAULT_URLS = [
    "https://github.com/arror1784/SkinAge/releases/download/v1.0.0/best_model.pth",
]


class _DownloadProgressBar:
    def __init__(self):
        self.pbar = None

    def __call__(self, block_num, block_size, total_size):
        if not self.pbar:
            try:
                from tqdm import tqdm
                self.pbar = tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading best_model.pth")
            except ImportError:
                self.pbar = False

        downloaded = block_num * block_size
        if self.pbar:
            self.pbar.update(block_size)
        else:
            if total_size > 0:
                percent = min(100.0, downloaded * 100.0 / total_size)
                mb_down = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                sys.stdout.write(f"\rDownloading model weights: {mb_down:.1f} MB / {mb_total:.1f} MB ({percent:.1f}%)")
                sys.stdout.flush()


def ensure_weights(target_path: Path | str | None = None, force: bool = False) -> Path:
    """Ensure that the trained model checkpoint exists, downloading if necessary.

    Parameters
    ----------
    target_path : Path | str, optional
        Target file path for best_model.pth. Defaults to outputs/models/best_model.pth.
    force : bool
        If True, re-downloads even if the file exists.

    Returns
    -------
    Path
        Absolute path to the downloaded/existing weight file.
    """
    target = Path(target_path) if target_path else _WEIGHTS_FILE
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_file() and not force:
        # Check minimum plausible size (at least 100 MB)
        if target.stat().st_size > 50 * 1024 * 1024:
            logger.info("Model weights already exist at: %s", target)
            return target

    print(f"\n[SkinAge] Model weights not found at {target}.")
    print(f"[SkinAge] Starting automatic download from GitHub Release mirror...")

    for url in _DEFAULT_URLS:
        try:
            print(f"Downloading from: {url}")
            progress = _DownloadProgressBar()
            urllib.request.urlretrieve(url, str(target), progress)
            if hasattr(progress, "pbar") and progress.pbar:
                progress.pbar.close()
            print(f"\n[SkinAge] Model weights successfully downloaded to: {target}\n")
            return target
        except Exception as exc:
            logger.warning("Failed downloading from %s: %s", url, exc)
            if target.is_file():
                target.unlink(missing_ok=True)

    logger.warning(
        "Could not download pre-trained weights automatically. "
        "Please ensure 'best_model.pth' is placed in '%s'.",
        target.parent,
    )
    return target


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ensure_weights(force="--force" in sys.argv)
