# Domestic Data Entry Operator — Class X

This folder contains an independently written textbook-style learning resource based on the topics and sequence of the Class X source textbook. The design follows the companion Class IX LaTeX book: A4 pages, compact spacing, framed borders, consistent running headers/footers and a teal/navy/gold palette.

## Build locally

Install a TeX distribution with XeLaTeX and the DejaVu fonts, then run:

```bash
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

This generates `main.pdf`.

## Download from GitHub Actions

Open the repository's **Actions** tab, select **Build Class X Book PDF**, open the latest successful workflow run and download the `Domestic-Data-Entry-Operator-Class-X-PDF` artifact ZIP. The workflow retains artifacts for 30 days.

The illustration PNG files referenced by `main.tex` must be present in `book_illustrations/`. The PDF is a study aid, not an official NCERT publication.
