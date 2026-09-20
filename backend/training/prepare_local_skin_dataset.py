"""Prepare a balanced five-class image set for local-only model training.

Images are selected from the public ``clinical-skin-disease-images`` manifest.
PAD images are grouped by patient before splitting. Exact duplicate image bytes
are removed globally. The generated data directory is ignored by Git.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.classifier.class_definitions import CLASS_PROFILES


REPOSITORY = "raghad-murad/clinical-skin-disease-images"
BASE_URL = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/main/"
MANIFEST_URL = BASE_URL + "metadata/clinical_final_master.csv?download=true"
USER_AGENT = "health-local-skin-trainer/2.0"
CLASS_ORDER = [item["short"] for item in CLASS_PROFILES["v3"]]


def fetch_bytes(url: str, attempts: int = 5) -> bytes:
    last_error = None
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(min(8, 2 ** attempt))
    raise RuntimeError(f"Download failed after {attempts} attempts: {url}") from last_error


def target_class(row: dict[str, str]) -> str | None:
    final_label = row["final_label"]
    original = row["original_class"].upper()
    filename = row["filename"].lower()
    direct_labels = {
        "Acne and Rosacea": "ACNE",
        "Bacterial Infections": "BACT",
        "Contact Dermatitis": "CONTACT",
        "Fungal Infections": "FUNGAL",
        "Herpes and STDs": "HERPES",
        "Psoriasis and Lichen Planus": "PSO",
        "Seborrheic Keratosis": "SEK",
        "Urticaria": "URT",
    }
    if final_label in direct_labels:
        return direct_labels[final_label]
    if original == "ACK":
        return "AK"
    if final_label == "Atopic Dermatitis":
        return "AD"
    if original == "BCC":
        return "BCC"
    if final_label == "Eczema":
        return "ECZEMA"
    if original == "MEL" or any(term in filename for term in ("malignant-melanoma", "lentigo-maligna")):
        return "MEL"
    if original == "SCC":
        return "SCC"
    if final_label == "Viral Infections" and any(
        term in filename for term in ("wart", "verruca", "mollusc")
    ):
        return "WARTS"
    return None


def group_id(row: dict[str, str]) -> str:
    if row["source_dataset"] == "PAD":
        match = re.search(r"PAD_PAT_(\d+)_", row["filename"], re.IGNORECASE)
        if match:
            return f"PAD_PAT_{match.group(1)}"
    return f"{row['source_dataset']}:{Path(row['filename']).stem}"


def select_and_split(rows: list[dict[str, str]], limit: int, seed: int) -> list[dict[str, str]]:
    by_class: dict[str, dict[str, list[dict[str, str]]]] = {
        key: defaultdict(list) for key in CLASS_ORDER
    }
    for row in rows:
        label = target_class(row)
        if label:
            row = {**row, "class_short": label, "group_id": group_id(row)}
            by_class[label][row["group_id"]].append(row)

    selected: list[dict[str, str]] = []
    for class_index, label in enumerate(CLASS_ORDER):
        groups = list(by_class[label].values())
        random.Random(seed + class_index).shuffle(groups)
        chosen: list[list[dict[str, str]]] = []
        count = 0
        for group in groups:
            if count >= limit:
                break
            chosen.append(group)
            count += len(group)

        targets = {"train": count * 0.70, "val": count * 0.85}
        running = 0
        for group in chosen:
            split = "train" if running < targets["train"] else "val" if running < targets["val"] else "test"
            selected.extend({**row, "split": split} for row in group)
            running += len(group)
    return selected


def download_row(row: dict[str, str], output: Path, reuse_from: Path | None) -> dict[str, str]:
    safe_name = hashlib.sha1(row["image_path"].encode("utf-8")).hexdigest()[:12]
    suffix = Path(row["filename"]).suffix.lower() or ".jpg"
    relative = Path("images") / row["class_short"] / f"{safe_name}{suffix}"
    destination = output / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.is_file():
        reusable = reuse_from / relative if reuse_from else None
        if reusable and reusable.is_file():
            shutil.copy2(reusable, destination)
        else:
            url = BASE_URL + urllib.parse.quote(row["image_path"], safe="/") + "?download=true"
            temporary = destination.with_suffix(destination.suffix + ".download")
            try:
                temporary.write_bytes(fetch_bytes(url))
                temporary.replace(destination)
            finally:
                temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    return {**row, "local_path": relative.as_posix(), "sha256": digest}


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare five-class local skin training data")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "data" / "local-skin-v3")
    parser.add_argument("--reuse-from", type=Path, default=Path(__file__).parent / "data" / "local-skin-v2")
    parser.add_argument("--limit-per-class", type=int, default=400)
    parser.add_argument("--seed", type=int, default=20260718)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()

    print("Loading cleaned dataset manifest...")
    text = fetch_bytes(MANIFEST_URL).decode("utf-8-sig")
    source_rows = list(csv.DictReader(io.StringIO(text)))
    selected = select_and_split(source_rows, args.limit_per_class, args.seed)
    rows_by_source_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in selected:
        rows_by_source_path[row["image_path"]].append(row)
    unique_selected = []
    conflicting_source_paths = 0
    for duplicates in rows_by_source_path.values():
        labels = {row["class_short"] for row in duplicates}
        if len(labels) > 1:
            conflicting_source_paths += 1
            continue
        unique_selected.append(sorted(duplicates, key=lambda row: row["split"])[0])
    selected = unique_selected
    print("Selected:", dict(Counter(row["class_short"] for row in selected)))
    print("Conflicting source paths removed:", conflicting_source_paths)

    args.output.mkdir(parents=True, exist_ok=True)
    completed: list[dict[str, str]] = []
    failed_rows: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(download_row, row, args.output, args.reuse_from): row
            for row in selected
        }
        for index, future in enumerate(as_completed(futures), 1):
            try:
                completed.append(future.result())
            except Exception:
                failed_rows.append(futures[future])
            if index % 100 == 0 or index == len(futures):
                print(f"Downloaded {index}/{len(futures)}")
    for row in failed_rows:
        completed.append(download_row(row, args.output, args.reuse_from))
    if failed_rows:
        print(f"Recovered transient failures: {len(failed_rows)}")

    rows_by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in completed:
        rows_by_hash[row["sha256"]].append(row)
    deduplicated = []
    conflicting_hashes = 0
    for duplicates in rows_by_hash.values():
        labels = {row["class_short"] for row in duplicates}
        if len(labels) > 1:
            conflicting_hashes += 1
            for row in duplicates:
                (args.output / row["local_path"]).unlink(missing_ok=True)
            continue
        keep, *discard = sorted(duplicates, key=lambda item: item["local_path"])
        deduplicated.append(keep)
        for row in discard:
            (args.output / row["local_path"]).unlink(missing_ok=True)

    manifest_path = args.output / "manifest.csv"
    fields = [
        "class_short", "split", "source_dataset", "original_class", "filename",
        "image_path", "group_id", "local_path", "sha256",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(deduplicated)
    license_path = args.output / "DATA_SOURCE.txt"
    license_path.write_text(
        f"Source: https://huggingface.co/datasets/{REPOSITORY}\n"
        "Use is subject to the source datasets' licenses and terms.\n",
        encoding="utf-8",
    )
    (args.output / "classes.json").write_text(
        json.dumps(CLASS_ORDER, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Ready:", manifest_path)
    print("Conflicting duplicate hashes removed:", conflicting_hashes)
    print("Final:", dict(Counter((row["class_short"], row["split"]) for row in deduplicated)))


if __name__ == "__main__":
    main()
