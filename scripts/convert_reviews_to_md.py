#!/usr/bin/env python3
"""Convert PDF review files to plain text or Markdown.

This script scans an input directory for `.pdf` files (e.g. `reviews/`),
extracts their text content, and writes corresponding `.txt` or `.md`
files to an output directory.

Dependencies
------------
Requires either `pypdf` or `PyPDF2`:

    pip install pypdf
    # or
    pip install PyPDF2

Usage
-----
    python scripts/convert_reviews_to_md.py \
        --input-dir reviews \
        --output-dir reviews/markdown \
        --format md

Arguments
---------
- --input-dir:  Directory containing PDF files (default: reviews)
- --output-dir: Directory to write converted files (default: reviews/markdown)
- --format:     "txt" or "md" (default: md)
"""

import argparse
import sys
from pathlib import Path
from typing import Optional


def _load_pdf_reader():
    """Try to import a PDF reader implementation.

    Prefers `pypdf`, falls back to `PyPDF2` if available.
    Exits with a clear message if neither is installed.
    """
    try:
        from pypdf import PdfReader  # type: ignore
        return PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
            return PdfReader
        except ImportError:
            print(
                "Error: could not import 'pypdf' or 'PyPDF2'.\n"
                "Install one of them, for example:\n\n"
                "    pip install pypdf\n\n"
                "and then re-run this script.",
                file=sys.stderr,
            )
            sys.exit(1)


def extract_text_from_pdf(pdf_path: Path, PdfReader) -> str:
    """Extract plain text from a PDF file.

    Parameters
    ----------
    pdf_path: Path
        Path to the PDF file.
    PdfReader: type
        PDF reader class (from pypdf or PyPDF2).

    Returns
    -------
    str
        Concatenated text from all pages.
    """
    reader = PdfReader(str(pdf_path))
    chunks = []

    # Different libraries expose pages slightly differently but both
    # pypdf and PyPDF2 support iteration over `pages` and `extract_text()`.
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Warning: failed to extract text from page in {pdf_path}: {exc}", file=sys.stderr)
            text = ""
        text = text.strip()
        if text:
            chunks.append(text)

    return "\n\n".join(chunks)


def convert_pdf_file(pdf_path: Path, output_dir: Path, fmt: str, PdfReader) -> Optional[Path]:
    """Convert a single PDF to .txt or .md.

    Returns the output path on success, or None if extraction failed.
    """
    text = extract_text_from_pdf(pdf_path, PdfReader)

    if not text.strip():
        print(f"Warning: no text extracted from {pdf_path}", file=sys.stderr)
        return None

    stem = pdf_path.stem

    if fmt == "txt":
        out_path = output_dir / f"{stem}.txt"
        content = text
    else:  # md
        out_path = output_dir / f"{stem}.md"
        # Simple heading with filename; body is raw extracted text.
        content = f"# {stem}\n\n" + text

    out_path.write_text(content, encoding="utf-8")
    return out_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert PDF review files to plain text or Markdown.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="reviews",
        help="Directory containing PDF files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reviews/markdown",
        help="Directory to write converted files",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["txt", "md"],
        default="md",
        help="Output format",
    )

    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: input directory does not exist or is not a directory: {input_dir}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    PdfReader = _load_pdf_reader()

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return 0

    print(f"Converting {len(pdf_files)} PDF file(s) from {input_dir} to {args.format} in {output_dir}...")

    successes = 0
    for pdf_path in pdf_files:
        out_path = convert_pdf_file(pdf_path, output_dir, args.format, PdfReader)
        if out_path is not None:
            successes += 1
            print(f"✓ {pdf_path.name} -> {out_path}")
        else:
            print(f"✗ Failed to convert {pdf_path}", file=sys.stderr)

    print(f"Done. Successfully converted {successes} / {len(pdf_files)} file(s).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
