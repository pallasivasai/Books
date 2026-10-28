# Final Book — Combined Handbook

This folder builds one continuous final handbook PDF by merging the eight source-book PDFs in a fixed order.
The generated output includes a table of contents followed by the eight source PDFs in sequence, with continuous header, footer, and page numbers across the full final PDF.

## Input order (8 source PDFs)
1. `../Domestic data entry operator-9th/Domestic data entry operator-9th.pdf`
2. `../Domestic data entry operator-10th/Domestic data entry operator-10th.pdf`
3. `../Web developer-11th/Web developer-11th.pdf`
4. `../Web developer-12th/Web developer-12th.pdf`
5. `../Artificial intelligence assistant-9th/Artificial intelligence assistant-9th.pdf`
6. `../Artificial intelligence assistant-10th/Artificial intelligence assistant-10th.pdf`
7. `../Junior software developer-11th/Junior software developer-11th.pdf`
8. `../Junior software developer-12th/Junior software developer-12th.pdf`

## Dependencies
- Python 3.10+
- LaTeX with `pdfpages` (for example TeX Live)
- `latexmk` (recommended for repeatable builds)

## Build commands
From repository root (`/home/runner/work/Books/Books`):

```bash
python "Final Book/merge_books.py"
cd "Final Book" && latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

Output PDF:
- `/home/runner/work/Books/Books/Final Book/main.pdf`

## Validation command (CI/local)
Use this to verify all eight inputs exist and `Final Book/main.tex` includes exactly those eight PDFs in order with `pdfpages`:

```bash
python "Final Book/merge_books.py" --check
```

## Troubleshooting
- **Missing source PDF/folder:** `merge_books.py` prints a clear list of missing paths and exits non-zero.
- **Multiple PDFs in one source folder:** keep one source PDF in that folder or restore the expected `<folder-name>.pdf` filename.
- **LaTeX compile failure:** ensure a LaTeX distribution is installed and that the `pdfpages` package is available.
- **Spaces in paths:** `main.tex` uses `\detokenize{...}` around PDF paths so folders with spaces work correctly.
