#!/usr/bin/env python3
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils import (
    read_docx,
    write_docx,
    apply_replacements,
    save_mapping,
    setup_logging,
)
from detector import detect_all
from replacer import ReplacementManager

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAPPING = str(PROJECT_ROOT / "mapping.json")


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PII Redaction Tool — detect and replace sensitive information in .docx files"
    )
    parser.add_argument("input_path", help="Path to the input .docx file")
    parser.add_argument("output_path", help="Path to save the redacted .docx file")
    parser.add_argument(
        "--mapping",
        default=DEFAULT_MAPPING,
        help="Path to the mapping.json file (default: mapping.json in project root)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    return parser


def ensure_directories(input_path: str, output_path: str) -> None:
    in_path = Path(input_path)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")
    out_dir = Path(output_path).parent
    if out_dir and not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)


def collect_all_text(doc) -> str:
    parts = []
    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if para.text.strip():
                        parts.append(para.text)
    for section in doc.sections:
        for header in [section.header, section.first_page_header, section.even_page_header]:
            if header is not None:
                for para in header.paragraphs:
                    if para.text.strip():
                        parts.append(para.text)
        for footer in [section.footer, section.first_page_footer, section.even_page_footer]:
            if footer is not None:
                for para in footer.paragraphs:
                    if para.text.strip():
                        parts.append(para.text)
    return "\n".join(parts)


def redact_document(
    input_path: str,
    output_path: str,
    mapping_path: str,
) -> dict:
    doc = read_docx(input_path)
    all_text = collect_all_text(doc)

    detector_results = detect_all(all_text)

    manager = ReplacementManager(mapping_path)
    manager.load()
    mapping = manager.build_mapping(detector_results)

    count = apply_replacements(doc, mapping)
    logger.info("Applied replacements to %d paragraphs/cells", count)

    write_docx(doc, output_path)
    save_mapping(mapping, mapping_path)
    return mapping


def main() -> None:
    parser = build_cli_parser()
    args = parser.parse_args()
    setup_logging(args.log_level)
    ensure_directories(args.input_path, args.output_path)

    logger.info("Starting PII redaction pipeline")
    logger.info("Input: %s", args.input_path)
    logger.info("Output: %s", args.output_path)
    logger.info("Mapping: %s", args.mapping)

    mapping = redact_document(args.input_path, args.output_path, args.mapping)

    logger.info("Redaction complete. %d replacements made.", len(mapping))
    logger.info("Redacted document saved to: %s", args.output_path)
    logger.info("Mapping saved to: %s", args.mapping)


if __name__ == "__main__":
    main()