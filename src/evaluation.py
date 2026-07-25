#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import setup_logging

logger = logging.getLogger(__name__)


def compute_metrics(
    true_positives: int,
    false_positives: int,
    false_negatives: int,
) -> dict:
    precision = _safe_division(true_positives, true_positives + false_positives)
    recall = _safe_division(true_positives, true_positives + false_negatives)
    f1 = _safe_division(2 * precision * recall, precision + recall)
    accuracy = _safe_division(
        true_positives, true_positives + false_positives + false_negatives
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "accuracy": accuracy,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def _safe_division(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def build_confusion_matrix(metrics: dict) -> str:
    tp = int(metrics["true_positives"])
    fp = int(metrics["false_positives"])
    fn = int(metrics["false_negatives"])
    header = "|                | Predicted PII | Predicted Non-PII |"
    sep = "|----------------|---------------|-------------------|"
    tp_row = f"| Actual PII     | {tp:<13} | {fn:<17} |"
    fn_row = f"| Actual Non-PII | {fp:<13} | {'-':>17} |"
    return "\n".join([header, sep, tp_row, fn_row])


def evaluate(
    detections: List[dict],
    ground_truth: List[dict],
    output_report: str = "evaluation_report.md",
) -> dict:
    gt_texts = {entry.get("text", "") for entry in ground_truth}
    det_texts = {entry.get("text", "") for entry in detections}

    true_positives = len(gt_texts & det_texts)
    false_positives = len(det_texts - gt_texts)
    false_negatives = len(gt_texts - det_texts)

    metrics = compute_metrics(true_positives, false_positives, false_negatives)
    report = generate_report(metrics, true_positives, false_positives, false_negatives)
    save_report(report, output_report)
    return metrics


def generate_report(
    metrics: dict,
    tp: int,
    fp: int,
    fn: int,
) -> str:
    lines = []
    lines.append("# PII Redaction Evaluation Report")
    lines.append("")
    lines.append("## Summary Metrics")
    lines.append("")
    lines.append(f"- **Precision**: {metrics['precision']}%")
    lines.append(f"- **Recall**: {metrics['recall']}%")
    lines.append(f"- **F1 Score**: {metrics['f1_score']}%")
    lines.append(f"- **Accuracy**: {metrics['accuracy']}%")
    lines.append("")
    lines.append("## Confusion Matrix")
    lines.append("")
    lines.append("```")
    lines.append(build_confusion_matrix(metrics))
    lines.append("```")
    lines.append("")
    lines.append("## Details")
    lines.append("")
    lines.append(f"- True Positives: {tp}")
    lines.append(f"- False Positives: {fp}")
    lines.append(f"- False Negatives: {fn}")
    lines.append("")
    return "\n".join(lines)


def save_report(report: str, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("Evaluation report saved to %s", output_path)


def load_ground_truth(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Loaded ground truth with %d entries", len(data))
    return data


def load_detections(mapping_path: str) -> list:
    with open(mapping_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    detections = []
    for original, replacement in data.items():
        detections.append({"original": original, "fake": replacement})
    logger.info("Loaded %d detections from mapping", len(detections))
    return detections


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate PII redaction results against ground truth"
    )
    parser.add_argument(
        "--ground-truth",
        required=True,
        help="Path to the ground truth JSON file",
    )
    parser.add_argument(
        "--mapping",
        default="mapping.json",
        help="Path to the mapping.json file (default: mapping.json)",
    )
    parser.add_argument(
        "--output",
        default="evaluation_report.md",
        help="Path to save the evaluation report (default: evaluation_report.md)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    return parser


def main() -> None:
    parser = build_cli_parser()
    args = parser.parse_args()
    setup_logging(args.log_level)

    ground_truth = load_ground_truth(args.ground_truth)
    detections = load_detections(args.mapping)

    metrics = evaluate(detections, ground_truth, args.output)

    print(f"Precision : {metrics['precision']}%")
    print(f"Recall    : {metrics['recall']}%")
    print(f"F1        : {metrics['f1_score']}%")
    print(f"Accuracy  : {metrics['accuracy']}%")
    logger.info("Evaluation report saved to %s", args.output)


if __name__ == "__main__":
    main()