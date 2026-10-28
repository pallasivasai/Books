from __future__ import annotations

import argparse
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

BOOKS = (
    SourceBook("Domestic data entry operator-9th", "Domestic Data Entry Operator"),
    SourceBook("Domestic data entry operator-10th", "Domestic Data Entry Operator"),
    SourceBook("Web developer-11th", "Web Development"),
    SourceBook("Web developer-12th", "Web Development"),
    SourceBook("Artificial intelligence assistant-9th", "Artificial Intelligence"),
    SourceBook("Artificial intelligence assistant-10th", "Artificial Intelligence"),
    SourceBook("Junior software developer-11th", "Junior Software Development"),
    SourceBook("Junior software developer-12th", "Junior Software Development"),
)

def source_tex(book: SourceBook) -> Path:
    path = ROOT / book.folder / "main.tex"
    if not path.is_file():
        raise FileNotFoundError(f"Missing source LaTeX file: {path}")
    return path

def extract_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.find(r"\mainmatter")
    if start >= 0:
        text = text[start + len(r"\mainmatter"):]
    else:
        start = text.find(r"\begin{document}")
        if start < 0:
            raise ValueError(f"No document body found in {path}")
        text = text[start + len(r"\begin{document}"):]
    # Remove per-book back matter and document terminators.
    text = re.split(r"\\backmatter\b|\\end\{document\}", text, maxsplit=1)[0]
    text = re.sub(r"\\frontmatter\b|\\mainmatter\b|\\tableofcontents\b", "", text)
    text = re.sub(r"(?m)^\s*\\appendix\s*$", "", text)
    # Remove the per-book running headers and page decorations if any source body repeats them.
    text = re.sub(r"\\thispagestyle\{[^}]*\}", "", text)
    # Images are retained, with paths redirected to their original source folders.
    folder = path.parent.name
    text = re.sub(
        r"(\\includegraphics(?:\[[^\]]*\])?\{)(?![^}]*[/\\\\])([^}]+)(\})",
        lambda m: m.group(1) + "../" + folder + "/" + m.group(2) + m.group(3),
        text,
    )
    text = re.sub(
        r"(\\includegraphics(?:\[[^\]]*\])?\{)([^}]*)(\})",
        lambda m: m.group(1) + (
            m.group(2) if m.group(2).startswith("../") else
            ("../" + folder + "/" + m.group(2) if not m.group(2).startswith("/") else m.group(2))
        ) + m.group(3),
        text,
    )
    # The book parts are stitched together without creating separate books or cover pages.
    return text.strip()

def render_main_tex(tex_path: Path) -> str:
    bodies = []
    for index, book in enumerate(BOOKS, start=1):
        path = source_tex(book)
        body = extract_body(path)
        # Keep the source chapter text and illustrations; only mark transitions between source curricula.
        bodies.append(
            "\n% ============================================================\n"
            f"% Curriculum sequence {index}: {book.title}\n"
            "% ============================================================\n"
            + body
        )

    body_text = "\n\n".join(bodies)
    return r"""\documentclass[11pt,openany,oneside]{book}
\usepackage[a4paper,top=20mm,bottom=20mm,left=22mm,right=22mm]{geometry}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\usepackage{amssymb,xcolor,graphicx,array,booktabs,longtable,tabularx,colortbl,enumitem,tikz,tcolorbox,titlesec,tocloft,hyperref,microtype,listings}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,calc}
\definecolor{Navy}{HTML}{17365D}
\definecolor{Teal}{HTML}{007F86}
\definecolor{Pale}{HTML}{EAF6F7}
\definecolor{Gold}{HTML}{E3A72F}
\definecolor{Ink}{HTML}{293746}
\definecolor{LightGold}{HTML}{FFF5DD}
\definecolor{SoftGray}{HTML}{F4F6F9}
\definecolor{Coral}{HTML}{D95D50}
\definecolor{Violet}{HTML}{7656A6}
\definecolor{Sky}{HTML}{DCEEFF}
\definecolor{Rose}{HTML}{FCEBE8}
\hypersetup{colorlinks=true,linkcolor=Teal,urlcolor=Teal,pdftitle={Combined Vocational Education Textbook},pdfauthor={Vocational Education}}
\setlist[itemize]{leftmargin=1.5em,itemsep=1.5pt,topsep=2pt,parsep=0pt}
\setlist[enumerate]{leftmargin=1.7em,itemsep=2pt,topsep=2pt,parsep=0pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt}
\setlength{\emergencystretch}{3em}
% No running headers, footers, page numbers, or decorative page borders.
\pagestyle{empty}
\titleformat{\chapter}[display]{\normalfont\sffamily\bfseries\color{Navy}}{\filleft\Large\color{Coral}\chaptername\ \thechapter}{.6ex}{\color{Teal}\LARGE\raggedright}
\titlespacing*{\chapter}{0pt}{-2mm}{.8ex}
\titleformat{\section}{\Large\sffamily\bfseries\color{Teal}}{\color{Coral}\thesection}{.7em}{}
\titleformat{\subsection}{\large\sffamily\bfseries\color{Violet}}{\thesubsection}{.7em}{}
\titlespacing*{\section}{0pt}{1.2ex plus .2ex minus .2ex}{.35ex}
\titlespacing*{\subsection}{0pt}{1ex plus .2ex minus .2ex}{.3ex}
\newcommand{\keyterm}[1]{\textbf{\color{Navy}#1}}
\newcommand{\checklistitem}{\noindent$\square$\quad}
\newcommand{\exampractice}[1]{\begin{tcolorbox}[colback=LightGold,colframe=Gold,boxrule=.6pt,arc=1.2mm,left=2mm,right=2mm,top=1mm,bottom=1mm]\textbf{Review questions.} #1\end{tcolorbox}}
\newcommand{\reviewtitle}{\par\noindent\textbf{\color{Navy}Review Questions}\par}
\newcommand{\review}[1]{\par\smallskip\reviewtitle\begin{enumerate}[label=\arabic*.,leftmargin=1.8em,itemsep=1pt,topsep=2pt]\small #1\end{enumerate}\smallskip}
\newcommand{\photo}[3]{\begin{center}\begin{tcolorbox}[colback=white,colframe=Teal!70,boxrule=.8pt,arc=1mm,left=2mm,right=2mm,top=2mm,bottom=2mm,width=.88\textwidth]\centering\IfFileExists{../Junior software developer-11th/images/#1}{\includegraphics[width=.92\linewidth,height=46mm,keepaspectratio]{../Junior software developer-11th/images/#1}}{\textbf{#2}}\end{tcolorbox}\end{center}{\small\textit{#3}}}
\begin{document}
\begin{titlepage}
\thispagestyle{empty}
\centering
\vspace*{25mm}
{\Huge\bfseries VOCATIONAL EDUCATION\par}
\vspace{5mm}
{\LARGE Combined Textbook\par}
\vspace{8mm}
{\large Data Entry \textbullet\ Web Development \textbullet\ Artificial Intelligence \textbullet\ Software Development\par}
\vfill
{\large Classes IX--XII\par}
\vspace{4mm}
{\normalsize A continuous learning volume\par}
\end{titlepage}
\pagenumbering{arabic}
\tableofcontents
\clearpage
""" + body_text + r"""

\end{document}
"""

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a continuous textbook from source LaTeX chapters.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    text = render_main_tex(output)
    if text.count(r"\begin{document}") != 1 or text.count(r"\end{document}") != 1:
        raise SystemExit("Generated source has invalid document boundaries.")
    if r"\includepdf" in text or r"\usepackage{pdfpages}" in text:
        raise SystemExit("PDF concatenation is not allowed in the continuous-book build.")
    output.write_text(text, encoding="utf-8")
    print(f"Generated continuous textbook source: {output}")
    print(f"Included {len(BOOKS)} curriculum source bodies in order.")

if __name__ == "__main__":
    main()
