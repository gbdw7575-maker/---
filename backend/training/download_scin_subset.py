"""Download a compact SCIN subset for common-condition model training.

The default profile selects the highest-weight dermatologist label for each
case, downloads only one image per case, and caps every target group. This
keeps the first training download reasonably small while preserving case-level
metadata for leakage-free splitting.
"""

import argparse
import ast
import csv
import io
import shutil
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


BUCKET = "https://storage.googleapis.com/dx-scin-public-data/"
CASES_URL = BUCKET + "dataset/scin_cases.csv"
LABELS_URL = BUCKET + "dataset/scin_labels.csv"
LICENSE_URL = "https://raw.githubusercontent.com/google-research-datasets/scin/main/LICENSE"

TARGET_GROUPS = {
    "eczema_dermatitis": {
        "Eczema",
        "Allergic Contact Dermatitis",
        "Irritant Contact Dermatitis",
        "Acute dermatitis, NOS",
        "CD - Contact dermatitis",
        "Seborrheic Dermatitis",
    },
    "psoriasis": {"Psoriasis"},
    "tinea_fungal": {"Tinea", "Tinea Versicolor"},
    "urticaria_bites": {"Urticaria", "Insect Bite"},
    "bacterial_infection": {"Folliculitis", "Impetigo", "Cellulitis", "Abscess"},
    "viral_lesion": {"Herpes Zoster", "Herpes Simplex", "Molluscum Contagiosum", "Verruca vulgaris"},
    "acne_rosacea": {"Acne", "Rosacea"},
    "scabies": {"Scabies"},
}


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8-sig")


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        return
    temporary = destination.with_suffix(destination.suffix + ".download")
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            with temporary.open("wb") as target:
                shutil.copyfileobj(response, target)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def build_label_lookup(labels_text: str, minimum_confidence: float):
    lookup = {}
    label_to_group = {
        label: group for group, labels in TARGET_GROUPS.items() for label in labels
    }
    for row in csv.DictReader(io.StringIO(labels_text)):
        raw_weights = row.get("weighted_skin_condition_label")
        if not raw_weights:
            continue
        weights = ast.literal_eval(raw_weights)
        if not weights:
            continue
        source_label, confidence = max(weights.items(), key=lambda item: item[1])
        target = label_to_group.get(source_label)
        if target and float(confidence) >= minimum_confidence:
            lookup[row["case_id"]] = (target, source_label, float(confidence))
    return lookup


def select_cases(cases_text: str, label_lookup: dict, limit_per_class: int):
    selected = []
    counts = defaultdict(int)
    for row in csv.DictReader(io.StringIO(cases_text)):
        label = label_lookup.get(row["case_id"])
        if not label:
            continue
        target, source_label, confidence = label
        if counts[target] >= limit_per_class:
            continue
        image_path = row.get("image_1_path")
        if not image_path:
            continue
        selected.append(
            {
                "case_id": row["case_id"],
                "target": target,
                "source_label": source_label,
                "confidence": confidence,
                "image_path": image_path,
                "fitzpatrick_skin_type": row.get("fitzpatrick_skin_type", ""),
                "age_group": row.get("age_group", ""),
            }
        )
        counts[target] += 1
    return selected, counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a compact common-condition SCIN subset")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data" / "scin-common")
    parser.add_argument("--limit-per-class", type=int, default=200)
    parser.add_argument("--minimum-confidence", type=float, default=0.40)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    print("Loading SCIN metadata...")
    cases_text = fetch_text(CASES_URL)
    labels_text = fetch_text(LABELS_URL)
    label_lookup = build_label_lookup(labels_text, args.minimum_confidence)
    selected, counts = select_cases(cases_text, label_lookup, args.limit_per_class)

    manifest_path = args.output / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=selected[0].keys() if selected else ["case_id"])
        writer.writeheader()
        writer.writerows(selected)
    download(LICENSE_URL, args.output / "SCIN_LICENSE.txt")

    for target, count in sorted(counts.items()):
        print(f"  {target}: {count}")
    print(f"Manifest: {manifest_path} ({len(selected)} cases)")
    if args.metadata_only:
        return

    def download_row(row):
        source_path = row["image_path"]
        suffix = Path(source_path).suffix or ".jpg"
        destination = args.output / "images" / row["target"] / f"{row['case_id']}{suffix}"
        download(BUCKET + source_path, destination)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        list(executor.map(download_row, selected))
    print(f"Downloaded {len(selected)} images to {args.output / 'images'}")


if __name__ == "__main__":
    main()
