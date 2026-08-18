#!/usr/bin/env python3
"""
prepare_dataset.py
End-to-end pipeline: Raw Images -> Face Alignment -> Landmarks -> Pseudo-labels -> 4ch Heatmaps -> Stratified Splits.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm
import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data.face_alignment import process_image
from src.data.pseudo_labels import (
    ScoreNormalizer,
    compute_wrinkle_score,
    compute_texture_score,
    compute_pigmentation_score,
    compute_redness_score,
    compute_dark_circle_score,
    generate_heatmaps,
    _extract_zone_crop_and_mask,
    CONCERN_TYPES,
)
from src.data.zone_extraction import _DEFAULT_ZONE_LANDMARKS, ZONE_NAMES
from src.data.dataset import QUALITY_SCORE_COLUMNS
from src.data.splits import create_splits, save_splits

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("prepare_dataset")


def build_zones_dict(config_path: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """Build zone definitions dict with merged landmark list and concern types."""
    if config_path and config_path.is_file():
        with open(config_path, "r", encoding="utf-8") as fh:
            raw_cfg = yaml.safe_load(fh) or {}
            raw_zones = raw_cfg.get("zones", {})
    else:
        raw_zones = {}

    zones: Dict[str, Dict[str, Any]] = {}
    for zone_name in ZONE_NAMES:
        zone_info = raw_zones.get(zone_name, {})
        # Concern types
        concerns = zone_info.get("concern_types", ["wrinkle", "pigmentation", "redness", "pore_texture"])
        # Ensure all 4 concerns are present for complete 28-score matrix
        for c in ["wrinkle", "pigmentation", "redness", "pore_texture"]:
            if c not in concerns:
                concerns.append(c)

        # Landmarks
        if "landmarks" in zone_info:
            lms = zone_info["landmarks"]
        elif "left" in zone_info and "right" in zone_info:
            lms = zone_info["left"]["landmarks"] + zone_info["right"]["landmarks"]
        else:
            # Flatten default landmarks list of lists
            default_lists = _DEFAULT_ZONE_LANDMARKS.get(zone_name, [[10, 338, 297]])
            lms = [idx for sublist in default_lists for idx in sublist]

        zones[zone_name] = {
            "landmarks": lms,
            "concern_types": concerns,
            "weight": zone_info.get("weight", 1.0),
        }
    return zones


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare dataset for SkinAge training.")
    parser.add_argument("--raw-dir", type=str, default="data/raw/utkface", help="Raw dataset directory.")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Processed output directory.")
    parser.add_argument("--max-samples", type=int, default=1500, help="Maximum number of samples to process (default: 1500).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    raw_path = (_PROJECT_ROOT / args.raw_dir).resolve()
    out_path = (_PROJECT_ROOT / args.output_dir).resolve()
    aligned_dir = out_path / "aligned"
    landmarks_dir = out_path / "landmarks"
    heatmaps_dir = out_path / "heatmaps"
    splits_dir = out_path / "splits"

    for d in [aligned_dir, landmarks_dir, heatmaps_dir, splits_dir]:
        d.mkdir(parents=True, exist_ok=True)

    metadata_csv = raw_path / "metadata.csv"
    if not metadata_csv.is_file():
        logger.error("Metadata CSV not found at %s", metadata_csv)
        return 1

    df_meta = pd.read_csv(metadata_csv)
    logger.info("Loaded metadata with %d entries from %s", len(df_meta), metadata_csv)

    if args.max_samples and len(df_meta) > args.max_samples:
        df_meta = df_meta.sample(n=args.max_samples, random_state=args.seed).reset_index(drop=True)
        logger.info("Subsampled to %d samples for training.", len(df_meta))

    zones = build_zones_dict(_PROJECT_ROOT / "config" / "zones_config.yaml")

    raw_records: List[Dict[str, Any]] = []
    raw_scores_by_concern: Dict[str, List[float]] = {c: [] for c in CONCERN_TYPES}

    logger.info("Processing images with MediaPipe alignment and feature extraction...")
    for _, row in tqdm(df_meta.iterrows(), total=len(df_meta), desc="Align & Pseudo-label"):
        img_path = Path(row["path"])
        if not img_path.is_file():
            continue

        stem = img_path.name.replace(".jpg.chip.jpg", "").replace(".jpg", "")

        aligned_file = aligned_dir / f"{stem}.png"
        landmarks_file = landmarks_dir / f"{stem}.npy"
        heatmap_file = heatmaps_dir / f"{stem}.npy"

        # 1. Face alignment & landmark detection
        if not aligned_file.is_file() or not landmarks_file.is_file():
            res = process_image(str(img_path), output_size=512)
            if res is None:
                continue
            aligned_bgr = res.aligned_image
            landmarks = res.landmarks
            cv2.imwrite(str(aligned_file), aligned_bgr)
            np.save(str(landmarks_file), landmarks)
        else:
            aligned_bgr = cv2.imread(str(aligned_file))
            landmarks = np.load(str(landmarks_file))

        if aligned_bgr is None or landmarks is None:
            continue

        # 2. Extract pseudo-labels per zone
        record: Dict[str, Any] = {
            "image_path": str(aligned_file),
            "heatmap_path": str(heatmap_file),
            "age": float(row.get("age", 25.0)),
            "gender": str(row.get("gender", "unknown")),
            "ethnicity": str(row.get("ethnicity", "unknown")),
        }

        # Compute zone raw scores
        for zone_name, z_cfg in zones.items():
            crop, mask, _ = _extract_zone_crop_and_mask(aligned_bgr, landmarks, z_cfg["landmarks"])
            for concern in CONCERN_TYPES:
                if concern == "wrinkle":
                    s, _ = compute_wrinkle_score(crop, mask)
                elif concern == "pigmentation":
                    s, _ = compute_pigmentation_score(crop, mask)
                elif concern == "redness":
                    s, _ = compute_redness_score(crop, mask)
                elif concern == "pore_texture":
                    s, _ = compute_texture_score(crop, mask)
                else:
                    s = 0.0

                record[f"{zone_name}_{concern}_raw"] = s
                raw_scores_by_concern[concern].append(s)

        # 3. Generate 4-channel heatmap (4, 512, 512)
        if not heatmap_file.is_file():
            heatmaps_dict = generate_heatmaps(aligned_bgr, landmarks, zones, output_size=512)
            # Stack into (4, 512, 512) float32 array in canonical CONCERN_TYPES order
            stacked_hm = np.stack([heatmaps_dict[c] for c in CONCERN_TYPES], axis=0).astype(np.float32)
            np.save(str(heatmap_file), stacked_hm)

        raw_records.append(record)

    if not raw_records:
        logger.error("No images successfully processed!")
        return 1

    logger.info("Successfully processed %d faces.", len(raw_records))
    df_processed = pd.DataFrame(raw_records)

    # 4. Normalise raw scores to 0-100 quality scores (100 = best, 0 = worst)
    normalizers: Dict[str, ScoreNormalizer] = {}
    for concern, val_list in raw_scores_by_concern.items():
        norm = ScoreNormalizer(invert=True)
        norm.fit(np.array(val_list, dtype=np.float64))
        normalizers[concern] = norm

    for zone_name in ZONE_NAMES:
        for concern in CONCERN_TYPES:
            raw_col = f"{zone_name}_{concern}_raw"
            norm_col = f"{zone_name}_{concern}"  # matches QUALITY_SCORE_COLUMNS
            df_processed[norm_col] = normalizers[concern].transform_array(df_processed[raw_col].to_numpy())

    # Add age_decade column for stratified splitting
    df_processed["age_decade"] = (df_processed["age"] // 10 * 10).astype(int)

    # 5. Create Stratified Splits
    logger.info("Creating stratified train / val / test splits...")
    train_df, val_df, test_df = create_splits(
        df_processed,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        seed=args.seed,
    )
    save_splits(train_df, val_df, test_df, str(splits_dir))
    logger.info("Splits saved to %s:", splits_dir)
    logger.info("  train: %d samples", len(train_df))
    logger.info("  val:   %d samples", len(val_df))
    logger.info("  test:  %d samples", len(test_df))

    logger.info("Dataset preparation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
