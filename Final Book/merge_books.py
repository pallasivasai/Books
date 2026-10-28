from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINAL_BOOK_DIR = ROOT / "Final Book"
DEFAULT_OUTPUT = FINAL_BOOK_DIR / "main.tex"


@dataclass(frozen=True)
class SourceBook:
    folder: str
    title: str


BOOKS: tuple[SourceBook, ...] = (
    SourceBook("Domestic data entry operator-9th", "Domestic Data Entry Operator — Class IX"),
    SourceBook("Domestic data entry operator-10th", "Domestic Data Entry Operator — Class X"),
    SourceBook("Web developer-11th", "Web Developer — Grade XI"),
    SourceBook("Web developer-12th", "Web Developer — Grade XII"),
    SourceBook("Artificial intelligence assistant-9th", "Artificial Intelligence Assistant — Grade IX"),
    SourceBook("Artificial intelligence assistant-10th", "Artificial Intelligence Assistant — Grade X"),
    SourceBook("Junior software developer-11th", "Junior Software Developer — Grade XI"),
    SourceBook("Junior software developer-12th", "Junior Software Developer — Grade XII"),
)


def resolve_book_pdf(book: SourceBook) -> Path:
    folder = ROOT / book.folder
    expected_pdf = folder / f"{book.folder}.pdf"
    if expected_pdf.exists():
        return expected_pdf

    discovered = sorted(folder.glob("*.pdf")) if folder.exists() else []
    if len(discovered) == 1:
        return discovered[0]
    if not folder.exists():
        raise FileNotFoundError(f"Missing source folder: {folder}")
    if not discovered:
        raise FileNotFoundError(
            f"Missing source PDF in {folder}. Expected {expected_pdf.name} or a single *.pdf file."
        )

    options = ", ".join(path.name for path in discovered)
    raise FileNotFoundError(
        f"Ambiguous PDFs in {folder}: {options}. Keep a single source PDF or restore {expected_pdf.name}."
    )


def collect_source_pdfs() -> list[tuple[SourceBook, Path]]:
    missing: list[str] = []
    resolved: list[tuple[SourceBook, Path]] = []
    for book in BOOKS:
        try:
            resolved.append((book, resolve_book_pdf(book)))
        except FileNotFoundError as exc:
            missing.append(str(exc))

    if missing:
        details = "\n- " + "\n- ".join(missing)
        raise SystemExit(f"Cannot build final book because required inputs are missing:{details}")

    return resolved


def rel_pdf_path(pdf_path: Path, tex_path: Path) -> str:
    return Path(os.path.relpath(pdf_path, tex_path.parent)).as_posix()


def render_main_tex(sources: list[tuple[SourceBook, Path]], tex_path: Path) -> str:
    toc_entries: list[str] = []
    include_entries: list[str] = []

    for book, pdf in sources:
        relative_path = rel_pdf_path(pdf, tex_path)
        toc_entries.append(
            f"\\chapter*{{{book.title}}}\n"
            f"\\addcontentsline{{toc}}{{chapter}}{{{book.title}}}\n"
            f"\\noindent\\texttt{{{relative_path}}}\\par"
        )
        include_entries.append(
            f"% {book.title}\n"
            f"\\includepdf[pages=-,pagecommand={{}}]{{\\detokenize{{{relative_path}}}}}"
        )

    toc_block = "\n\n".join(toc_entries)
    include_block = "\n\n".join(include_entries)

    return (
        "\\documentclass[11pt,openany,oneside]{book}\n"
        "\\usepackage[a4paper,margin=20mm]{geometry}\n"
        "\\usepackage{pdfpages}\n"
        "\\usepackage[hidelinks]{hyperref}\n\n"
        "\\begin{document}\n"
        "\\begin{titlepage}\n"
        "\\centering\n"
        "{\\LARGE\\bfseries HANDBOOK\\par}\n"
        "\\vspace{8mm}\n"
        "{\\Large Combined Vocational Education Textbooks\\par}\n"
        "\\vspace{3mm}\n"
        "{\\large Classes IX--XII\\par}\n"
        "\\vfill\n"
        "{\\large Data Entry $\\bullet$ Web Development $\\bullet$ Artificial Intelligence $\\bullet$ Software Development\\par}\n"
        "\\end{titlepage}\n\n"
        "\\frontmatter\n"
        "\\tableofcontents\n"
        "\\mainmatter\n\n"
        f"{toc_block}\n\n"
        "\\cleardoublepage\n"
        f"{include_block}\n"
        "\\end{document}\n"
    )


def validate_generated_structure(tex_text: str, sources: list[tuple[SourceBook, Path]], tex_path: Path) -> list[str]:
    errors: list[str] = []

    if "\\usepackage{pdfpages}" not in tex_text:
        errors.append("main.tex is missing \\usepackage{pdfpages}.")

    include_pattern = re.compile(
        r"\\includepdf\[pages=-,pagecommand=\{\}\]\{\\detokenize\{([^}]*)\}\}"
    )
    included_paths = include_pattern.findall(tex_text)

    if len(included_paths) != len(sources):
        errors.append(
            f"Expected {len(sources)} include entries with pages=- and pagecommand={{}}, found {len(included_paths)}."
        )

    expected_paths = [rel_pdf_path(pdf, tex_path) for _, pdf in sources]
    if included_paths != expected_paths:
        errors.append(
            "Included PDF order/content mismatch.\n"
            f"Expected: {expected_paths}\n"
            f"Found:    {included_paths}"
        )

    return errors


def write_main_tex(tex_path: Path) -> None:
    sources = collect_source_pdfs()
    tex_text = render_main_tex(sources, tex_path)
    errors = validate_generated_structure(tex_text, sources, tex_path)
    if errors:
        raise SystemExit("Generated TeX failed structural validation:\n- " + "\n- ".join(errors))

    tex_path.parent.mkdir(parents=True, exist_ok=True)
    tex_path.write_text(tex_text, encoding="utf-8")
    print(f"Generated {tex_path} from {len(sources)} source PDFs.")


def check_main_tex(tex_path: Path) -> None:
    sources = collect_source_pdfs()
    if not tex_path.exists():
        raise SystemExit(f"main.tex not found: {tex_path}")

    tex_text = tex_path.read_text(encoding="utf-8")
    errors = validate_generated_structure(tex_text, sources, tex_path)
    if errors:
        raise SystemExit("Structural validation failed:\n- " + "\n- ".join(errors))

    print("Validation successful:")
    for _, pdf in sources:
        print(f"- {rel_pdf_path(pdf, tex_path)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or validate the final merged-book LaTeX source.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output TeX path (default: Final Book/main.tex)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate source PDFs and the existing main.tex structure without writing files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output
    if not output.is_absolute():
        output = ROOT / output

    if args.check:
        check_main_tex(output)
        return

    write_main_tex(output)


if __name__ == "__main__":
    main()
