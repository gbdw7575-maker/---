"""Train and export the local-only five-class skin image model."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
from collections import Counter
from pathlib import Path

TRAINING_DIR = Path(__file__).resolve().parent
os.environ.setdefault("TORCH_HOME", str(TRAINING_DIR / ".torch"))

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms


CLASS_ORDER: list[str] = []
CLASS_TO_INDEX: dict[str, int] = {}
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


class ManifestDataset(Dataset):
    def __init__(self, root: Path, rows: list[dict[str, str]], transform):
        self.root = root
        self.rows = rows
        self.transform = transform

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int):
        row = self.rows[index]
        with Image.open(self.root / row["local_path"]) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, CLASS_TO_INDEX[row["class_short"]]


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)


def make_transforms():
    normalize = transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
    train = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.72, 1.0), ratio=(0.80, 1.25)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.18, contrast=0.18, saturation=0.12, hue=0.02),
        transforms.ToTensor(),
        normalize,
        transforms.RandomErasing(p=0.15, scale=(0.02, 0.08), ratio=(0.5, 2.0)),
    ])
    evaluate = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        normalize,
    ])
    return train, evaluate


def build_model(architecture: str) -> nn.Module:
    if architecture == "mobilenet_v3_small":
        model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
        model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, len(CLASS_ORDER))
        return model
    if architecture == "efficientnet_b0":
        model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, len(CLASS_ORDER))
        return model
    raise ValueError(f"Unsupported architecture: {architecture}")


def metrics(logits: torch.Tensor, targets: torch.Tensor) -> tuple[int, int, list[int], list[int]]:
    top = logits.topk(3, dim=1).indices
    top1 = int((top[:, 0] == targets).sum().item())
    top3 = int((top == targets[:, None]).any(dim=1).sum().item())
    correct = [0] * len(CLASS_ORDER)
    totals = [0] * len(CLASS_ORDER)
    for expected, predicted in zip(targets.tolist(), top[:, 0].tolist()):
        totals[expected] += 1
        correct[expected] += int(expected == predicted)
    return top1, top3, correct, totals


def run_epoch(model, loader, loss_fn, device, optimizer=None) -> dict:
    training = optimizer is not None
    model.train(training)
    loss_sum = top1 = top3 = count = 0
    class_correct = [0] * len(CLASS_ORDER)
    class_total = [0] * len(CLASS_ORDER)
    context = torch.enable_grad() if training else torch.inference_mode()
    with context:
        for images, targets in loader:
            images, targets = images.to(device), targets.to(device)
            if training:
                optimizer.zero_grad(set_to_none=True)
            logits = model(images)
            loss = loss_fn(logits, targets)
            if training:
                loss.backward()
                optimizer.step()
            batch_top1, batch_top3, correct, totals = metrics(logits, targets)
            batch_size = targets.shape[0]
            loss_sum += float(loss.item()) * batch_size
            top1 += batch_top1
            top3 += batch_top3
            count += batch_size
            class_correct = [a + b for a, b in zip(class_correct, correct)]
            class_total = [a + b for a, b in zip(class_total, totals)]
    recalls = [class_correct[i] / class_total[i] if class_total[i] else 0.0 for i in range(len(CLASS_ORDER))]
    return {
        "loss": loss_sum / max(1, count),
        "top1": top1 / max(1, count),
        "top3": top3 / max(1, count),
        "macro_recall": sum(recalls) / len(recalls),
        "class_recall": dict(zip(CLASS_ORDER, recalls)),
    }


class RuntimeExport(nn.Module):
    """Accept runtime NHWC [-1, 1] input and return probabilities."""

    def __init__(self, model: nn.Module):
        super().__init__()
        self.model = model
        self.register_buffer("mean", torch.tensor(IMAGENET_MEAN).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor(IMAGENET_STD).view(1, 3, 1, 1))

    def forward(self, images):
        images = images.permute(0, 3, 1, 2)
        images = ((images + 1.0) * 0.5 - self.mean) / self.std
        return torch.softmax(self.model(images), dim=1)


def export_onnx(model: nn.Module, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".onnx.tmp")
    wrapper = RuntimeExport(model.cpu().eval())
    dummy = torch.zeros(1, 224, 224, 3)
    torch.onnx.export(
        wrapper,
        (dummy,),
        temporary,
        input_names=["images"],
        output_names=["probabilities"],
        dynamic_axes={"images": {0: "batch"}, "probabilities": {0: "batch"}},
        opset_version=18,
        dynamo=False,
    )
    temporary.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the local five-class skin model")
    parser.add_argument("--data", type=Path, default=TRAINING_DIR / "data" / "local-skin-v3")
    parser.add_argument("--output", type=Path, default=TRAINING_DIR.parent / "app" / "classifier" / "weights" / "skin_disease_expanded_v3.onnx")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--head-epochs", type=int, default=2)
    parser.add_argument("--fine-tune-epochs", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--architecture", choices=("mobilenet_v3_small", "efficientnet_b0"), default="efficientnet_b0")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260718)
    args = parser.parse_args()
    seed_everything(args.seed)

    with (args.data / "manifest.csv").open(encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    global CLASS_ORDER, CLASS_TO_INDEX
    classes_path = args.data / "classes.json"
    CLASS_ORDER = (
        json.loads(classes_path.read_text(encoding="utf-8"))
        if classes_path.is_file()
        else sorted({row["class_short"] for row in rows})
    )
    CLASS_TO_INDEX = {label: index for index, label in enumerate(CLASS_ORDER)}
    unknown_classes = sorted({row["class_short"] for row in rows} - set(CLASS_ORDER))
    if unknown_classes:
        raise ValueError(f"Manifest contains classes missing from classes.json: {unknown_classes}")
    by_split = {split: [row for row in rows if row["split"] == split] for split in ("train", "val", "test")}
    print("Dataset:", {split: dict(Counter(row["class_short"] for row in items)) for split, items in by_split.items()})

    train_transform, eval_transform = make_transforms()
    loaders = {
        "train": DataLoader(ManifestDataset(args.data, by_split["train"], train_transform), batch_size=args.batch_size, shuffle=True, num_workers=args.workers),
        "val": DataLoader(ManifestDataset(args.data, by_split["val"], eval_transform), batch_size=args.batch_size, shuffle=False, num_workers=args.workers),
        "test": DataLoader(ManifestDataset(args.data, by_split["test"], eval_transform), batch_size=args.batch_size, shuffle=False, num_workers=args.workers),
    }
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)
    model = build_model(args.architecture)
    model.to(device)
    train_counts = Counter(row["class_short"] for row in by_split["train"])
    class_weights = torch.tensor(
        [len(by_split["train"]) / (len(CLASS_ORDER) * train_counts[label]) for label in CLASS_ORDER],
        dtype=torch.float32,
        device=device,
    )
    print("Class weights:", dict(zip(CLASS_ORDER, class_weights.cpu().tolist())))
    loss_fn = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.08)

    best_score = -1.0
    best_state = None
    history = []
    phases = [("head", args.head_epochs, args.learning_rate), ("fine_tune", args.fine_tune_epochs, args.learning_rate * 0.25)]
    started = time.time()
    for phase, epochs, learning_rate in phases:
        for parameter in model.features.parameters():
            parameter.requires_grad = phase == "fine_tune"
        optimizer = torch.optim.AdamW(
            (parameter for parameter in model.parameters() if parameter.requires_grad),
            lr=learning_rate,
            weight_decay=1e-4,
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs))
        for epoch in range(1, epochs + 1):
            train_result = run_epoch(model, loaders["train"], loss_fn, device, optimizer)
            val_result = run_epoch(model, loaders["val"], loss_fn, device)
            scheduler.step()
            score = (val_result["top1"] + val_result["macro_recall"]) / 2
            history.append({"phase": phase, "epoch": epoch, "train": train_result, "val": val_result})
            print(phase, epoch, "train", train_result, "val", val_result)
            if score > best_score:
                best_score = score
                best_state = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}

    if best_state is None:
        raise RuntimeError("Training did not produce a checkpoint")
    model.load_state_dict(best_state)
    model.to(device)
    test_result = run_epoch(model, loaders["test"], loss_fn, device)
    print("Test:", test_result)
    export_onnx(model, args.output)
    report = {
        "classes": CLASS_ORDER,
        "architecture": f"torchvision-{args.architecture.replace('_', '-')}",
        "seed": args.seed,
        "device": str(device),
        "duration_seconds": round(time.time() - started, 1),
        "best_validation_score": best_score,
        "test": test_result,
        "history": history,
    }
    report_path = args.output.with_suffix(".training.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("ONNX:", args.output)
    print("Report:", report_path)


if __name__ == "__main__":
    main()
