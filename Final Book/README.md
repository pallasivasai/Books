# Final Book — Combined Handbook

This folder contains the build script for one combined handbook PDF. The original eight book folders are inputs only and are not edited.

## Book order
1. Domestic Data Entry Operator — Class IX
2. Domestic Data Entry Operator — Class X
3. Web Developer — Grade XI
4. Web Developer — Grade XII
5. Artificial Intelligence Assistant — Grade IX
6. Artificial Intelligence Assistant — Grade X
7. Junior Software Developer — Grade XI
8. Junior Software Developer — Grade XII

## Build
The GitHub Actions workflow at `.github/workflows/build-final-book.yml` downloads the image assets used by the original books, generates the Class X diagrams, merges the eight LaTeX sources into one document, and compiles it with XeLaTeX. The PDF is published as a workflow artifact named `Final-Combined-Handbook-PDF`.

Run it from GitHub: **Actions → Build Final Combined Handbook → Run workflow**.
