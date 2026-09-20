"""Download dermatologist-labelled SCIN images and evaluate the skin classifier.

This is a small external smoke test, not a clinical validation study.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.classifier.model import SkinClassifier  # noqa: E402


ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"
DATASET_PAGE_SIZE = 100
TARGET_LABELS = {
    "AD": {"Atopic Dermatitis", "Atopic dermatitis"},
    "BCC": {"Basal Cell Carcinoma", "Basal cell carcinoma"},
    "ECZEMA": {"Eczema"},
    "MEL": {"Melanoma"},
    "WARTS": {
        "Molluscum Contagiosum",
        "Molluscum contagiosum",
        "Verruca Vulgaris",
        "Verruca vulgaris",
        "Warts",
    },
}

CLINICAL_DATASET_REPO = "raghad-murad/clinical-skin-disease-images"
CLINICAL_SAMPLE_PATHS = {
    "AD": [
        "Atopic Dermatitis/DER_05ATopicAreola.jpg",
        "Atopic Dermatitis/DER_05Atopic.jpg",
        "Atopic Dermatitis/DER_05Atopic010203.jpg",
    ],
    "BCC": [
        "Basal Cell Carcinoma/PAD_PAT_101_1041_651.jpg",
        "Basal Cell Carcinoma/PAD_PAT_101_1041_658.jpg",
        "Basal Cell Carcinoma/PAD_PAT_101_1041_898.jpg",
    ],
    "ECZEMA": [
        "Eczema/DER_03Eczema0915.jpg",
        "Eczema/DER_03EczemaExcoriated.jpg",
        "Eczema/DER_03EczemaExcoriated011204.jpg",
    ],
    "MEL": [
        "Melanoma and Nevi/DER_malignant-melanoma-1.jpg",
        "Melanoma and Nevi/DER_malignant-melanoma-10.jpg",
        "Melanoma and Nevi/DER_malignant-melanoma-100.jpg",
    ],
    "WARTS": [
        "Viral Infections/DER_12WartAldara.jpg",
        "Viral Infections/DER_12WartNitrogen1.jpg",
        "Viral Infections/DER_12WartPeriungual.jpg",
    ],
}


def request_json(url: str) -> dict:
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "health-skin-evaluator/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError("unreachable")


def collect_scin_samples(per_class: int) -> dict[str, list[dict]]:
    selected: dict[str, list[dict]] = defaultdict(list)
    def fetch_page(offset: int) -> dict:
        query = urllib.parse.urlencode({
            "dataset": "google/scin",
            "config": "train",
            "split": "train",
            "offset": offset,
            "length": DATASET_PAGE_SIZE,
        })
        return request_json(f"{ROWS_ENDPOINT}?{query}")

    first_page = fetch_page(0)
    total = first_page.get("num_rows_total", 0)
    pages = [first_page]
    offsets = list(range(DATASET_PAGE_SIZE, total, DATASET_PAGE_SIZE))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        pages.extend(executor.map(fetch_page, offsets))

    all_rows = sorted(
        (item for page in pages for item in page.get("rows", [])),
        key=lambda item: item["row_idx"],
    )
    for item in all_rows:
            row = item["row"]
            try:
                labels = ast.literal_eval(row.get("dermatologist_skin_condition_on_label_name") or "[]")
                confidence = ast.literal_eval(row.get("dermatologist_skin_condition_confidence") or "[]")
            except (SyntaxError, ValueError):
                continue
            if not labels or not confidence or confidence[0] < 4:
                continue
            image = row.get("image_1_path") or {}
            if not image.get("src"):
                continue
            for class_short, accepted_labels in TARGET_LABELS.items():
                if labels[0] in accepted_labels and len(selected[class_short]) < per_class:
                    selected[class_short].append({
                        "row_index": item["row_idx"],
                        "case_id": row.get("case_id"),
                        "label": labels[0],
                        "label_confidence": confidence[0],
                        "image_url": image["src"],
                    })
                    break
    return selected


def collect_clinical_samples(per_class: int) -> dict[str, list[dict]]:
    selected = {}
    for class_short, paths in CLINICAL_SAMPLE_PATHS.items():
        selected[class_short] = []
        for index, path in enumerate(paths[:per_class]):
            encoded_path = urllib.parse.quote(path)
            selected[class_short].append({
                "row_index": index,
                "case_id": path,
                "label": class_short,
                "label_confidence": "directory_and_filename",
                "image_url": (
                    f"https://huggingface.co/datasets/{CLINICAL_DATASET_REPO}"
                    f"/resolve/main/{encoded_path}?download=true"
                ),
            })
    return selected


def download_samples(samples: dict[str, list[dict]], image_dir: Path) -> list[dict]:
    image_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for class_short, items in samples.items():
        for item in items:
            path = image_dir / f"{class_short}_{item['row_index']}.jpg"
            request = urllib.request.Request(item["image_url"], headers={"User-Agent": "health-skin-evaluator/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                path.write_bytes(response.read())
            downloaded.append({**item, "expected": class_short, "path": str(path)})
    return downloaded


def evaluate_local(samples: list[dict]) -> list[dict]:
    classifier = SkinClassifier()
    results = []
    for sample in samples:
        with Image.open(sample["path"]) as image:
            prediction = classifier.predict(image.convert("RGB"), topk=5)
        codes = [item["class_short"] for item in prediction.get("predictions", [])]
        results.append({
            **sample,
            "predictions": prediction.get("predictions", []),
            "top1": codes[0] if codes else None,
            "top3": codes[:3],
            "top1_probability": prediction["predictions"][0]["probability"] if codes else None,
            "top1_correct": bool(codes and codes[0] == sample["expected"]),
            "top3_correct": sample["expected"] in codes[:3],
        })
    return results


def summarize(results: list[dict]) -> dict:
    count = len(results)
    by_class = {}
    for class_short in TARGET_LABELS:
        class_results = [item for item in results if item["expected"] == class_short]
        by_class[class_short] = {
            "count": len(class_results),
            "top1_correct": sum(item["top1_correct"] for item in class_results),
            "top3_correct": sum(item["top3_correct"] for item in class_results),
            "predicted_top1": dict(Counter(item["top1"] for item in class_results)),
        }
    return {
        "count": count,
        "top1_correct": sum(item["top1_correct"] for item in results),
        "top1_accuracy": round(sum(item["top1_correct"] for item in results) / count, 4) if count else None,
        "top3_correct": sum(item["top3_correct"] for item in results),
        "top3_accuracy": round(sum(item["top3_correct"] for item in results) / count, 4) if count else None,
        "by_class": by_class,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-class", type=int, default=3)
    parser.add_argument("--source", choices=("clinical", "scin"), default="clinical")
    parser.add_argument("--output-dir", type=Path, default=BACKEND_DIR / "evaluation" / "skin_online")
    args = parser.parse_args()

    samples = (
        collect_scin_samples(args.per_class)
        if args.source == "scin"
        else collect_clinical_samples(args.per_class)
    )
    downloaded = download_samples(samples, args.output_dir / "images")
    local_results = evaluate_local(downloaded)
    report = {
        "dataset": "google/scin" if args.source == "scin" else CLINICAL_DATASET_REPO,
        "selection": (
            "Primary dermatologist label in supported class with confidence >= 4/5"
            if args.source == "scin"
            else "Category directory plus disease-specific filename"
        ),
        "requested_per_class": args.per_class,
        "downloaded_per_class": {key: len(value) for key, value in samples.items()},
        "local_model": summarize(local_results),
        "samples": [
            {key: value for key, value in item.items() if key != "image_url"}
            for item in local_results
        ],
    }
    report_path = args.output_dir / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
