from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BOOKS = [
    ("Domestic data entry operator-9th", "Domestic Data Entry Operator — Class IX"),
    ("Domestic data entry operator-10th", "Domestic Data Entry Operator — Class X"),
    ("Web developer-11th", "Web Developer — Grade XI"),
    ("Web developer-12th", "Web Developer — Grade XII"),
    ("Artificial intelligence assistant-9th", "Artificial Intelligence Assistant — Grade IX"),
    ("Artificial intelligence assistant-10th", "Artificial Intelligence Assistant — Grade X"),
    ("Junior software developer-11th", "Junior Software Developer — Grade XI"),
    ("Junior software developer-12th", "Junior Software Developer — Grade XII"),
]

def get_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if r"\mainmatter" in text:
        text = text.split(r"\mainmatter", 1)[1]
    elif r"\tableofcontents" in text:
        text = text.split(r"\tableofcontents", 1)[1]
    elif r"\begin{document}" in text:
        text = text.split(r"\begin{document}", 1)[1]
    text = re.sub(r"\\end\{document\}.*$", "", text, flags=re.S)
    text = re.sub(r"\\begin\{titlepage\}.*?\\end\{titlepage\}", "", text, flags=re.S)
    text = re.sub(r"\\frontmatter|\\mainmatter|\\backmatter|\\tableofcontents|\\appendix", "", text)
    text = re.sub(r"\{book_illustrations/", "{../" + path.parent.name + r"/book_illustrations/", text)
    text = re.sub(r"\{images/", "{../" + path.parent.name + r"/images/", text)

    def guarded(match):
        options = match.group(1) or ""
        image_path = match.group(2)
        if "#" in image_path:
            return match.group(0)
        label = Path(image_path).name.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        return (r"\IfFileExists{" + image_path + "}{" + r"\includegraphics" + options +
                "{" + image_path + "}}{\\begin{center}\\fbox{\\parbox[c][28mm][c]{.76\\textwidth}{\\centering\\small Illustration not available: " +
                label + "}}\\end{center}}")
    text = re.sub(r"\\includegraphics(\[[^\]]*\])?\{([^}]+)\}", guarded, text)
    text = re.sub(r"\\photo\{([^}]+)\}", lambda m: r"\photo{../" + path.parent.name + "/images/" + m.group(1) + "}", text)
    return text.strip()

def main():
    sections = []
    seen_chapters = set()
    for folder, label in BOOKS:
        src = ROOT / folder / "main.tex"
        if not src.exists():
            raise SystemExit(f"Missing source file: {src}")
        body = get_body(src)
        chunks = re.split(r"(?=\\chapter\*?(?:\[[^]]*\])?\{)", body)
        kept = []
        for chunk in chunks:
            match = re.search(r"\\chapter\*?(?:\[[^]]*\])?\{([^}]*)\}", chunk)
            if not match:
                if chunk.strip():
                    kept.append(chunk)
                continue
            title = match.group(1).strip().casefold()
            normalized = re.sub(r"%[^\n]*", "", chunk)
            normalized = re.sub(r"\s+", " ", normalized).strip()
            key = (title, normalized)
            if key not in seen_chapters:
                seen_chapters.add(key)
                kept.append(chunk)
        sections.append(r"\part*{" + label + "}" + "\n" +
                        r"\addcontentsline{toc}{part}{" + label + "}" + "\n\n" +
                        "\n\n".join(kept))

    preamble = r"""\documentclass[11pt,openany,oneside]{book}
\usepackage[a4paper,top=25mm,bottom=23mm,left=25mm,right=22mm,headheight=22pt]{geometry}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\usepackage{amssymb,xcolor,graphicx,array,booktabs,longtable,tabularx,colortbl,enumitem,tikz,tcolorbox,fancyhdr,titlesec,tocloft,hyperref,eso-pic,microtype,listings}
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
\hypersetup{colorlinks=true,linkcolor=Teal,urlcolor=Teal,pdftitle={HANDBOOK — Combined Vocational Education Textbooks},pdfauthor={Vocational Education Handbook}}
\setlist[itemize]{leftmargin=1.5em,itemsep=1.5pt,topsep=2pt,parsep=0pt}
\setlist[enumerate]{leftmargin=1.7em,itemsep=2pt,topsep=2pt,parsep=0pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt}
\setlength{\emergencystretch}{3em}
\AddToShipoutPictureBG{\begin{tikzpicture}[remember picture,overlay]
\draw[Navy!65,line width=.55pt] ([xshift=11mm,yshift=-11mm]current page.north west) rectangle ([xshift=-11mm,yshift=11mm]current page.south east);
\draw[Teal,line width=1.6pt] ([xshift=11mm,yshift=-11mm]current page.north west)--([xshift=37mm,yshift=-11mm]current page.north west);
\draw[Coral,line width=1.6pt] ([xshift=-11mm,yshift=11mm]current page.south east)--([xshift=-37mm,yshift=11mm]current page.south east);
\fill[Gold] ([xshift=11mm,yshift=-11mm]current page.north west) circle (1.1mm);
\fill[Violet] ([xshift=-11mm,yshift=11mm]current page.south east) circle (1.1mm);
\end{tikzpicture}}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\bfseries\sffamily\color{Teal} VOCATIONAL EDUCATION}
\fancyhead[R]{\small\sffamily\color{Navy} HANDBOOK}
\fancyfoot[C]{\tikz[baseline=(n.base)]\node[fill=Teal,draw=Gold,line width=.7pt,text=white,circle,minimum size=7mm,inner sep=1pt,font=\small\bfseries] (n) {\thepage};}
\renewcommand{\headrulewidth}{.5pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{Gold}\leaders\hrule height \headrulewidth\hfill}}
\fancypagestyle{plain}{\fancyhf{}\fancyhead[L]{\small\bfseries\sffamily\color{Teal} VOCATIONAL EDUCATION}\fancyhead[R]{\small\sffamily\color{Navy} HANDBOOK}\fancyfoot[C]{\tikz[baseline=(n.base)]\node[fill=Teal,draw=Gold,line width=.7pt,text=white,circle,minimum size=7mm,inner sep=1pt,font=\small\bfseries] (n) {\thepage};}\renewcommand{\headrulewidth}{.5pt}}
\titleformat{\chapter}[display]{\normalfont\sffamily\bfseries\color{Navy}}{\filleft\Large\color{Coral}\chaptername\ \thechapter}{.6ex}{\color{Teal}\LARGE\raggedright}[\vspace{.5ex}\color{Gold}\rule{\textwidth}{.8pt}]
\titlespacing*{\chapter}{0pt}{-8mm}{.5ex}
\titleformat{\section}{\Large\sffamily\bfseries\color{Teal}}{\color{Coral}\thesection}{.7em}{}
\titleformat{\subsection}{\large\sffamily\bfseries\color{Violet}}{\thesubsection}{.7em}{}
\titlespacing*{\section}{0pt}{1.2ex plus .2ex minus .2ex}{.35ex}
\titlespacing*{\subsection}{0pt}{1ex plus .2ex minus .2ex}{.3ex}
\newcommand{\keyterm}[1]{\textbf{\color{Navy}#1}}
\newcommand{\checklistitem}{\noindent$\square$\quad}
\newcommand{\exampractice}[1]{\begin{tcolorbox}[colback=LightGold,colframe=Gold,boxrule=.6pt,arc=1.2mm,left=2mm,right=2mm,top=1mm,bottom=1mm]\textbf{Think and answer.} #1\end{tcolorbox}}
\newcommand{\reviewtitle}{\par\noindent\textbf{\color{Navy}Review Questions}\par}
\newcommand{\photo}[3]{\begin{center}\begin{tcolorbox}[colback=white,colframe=Teal!70,boxrule=.8pt,arc=1mm,left=2mm,right=2mm,top=2mm,bottom=2mm,width=.88\textwidth]\centering\IfFileExists{#1}{\includegraphics[width=.92\linewidth,height=46mm,keepaspectratio]{#1}}{\vspace{8mm}\textbf{#2}\par\small Visual example for this topic\vspace{8mm}}\end{tcolorbox}\end{center}{\small\textit{#3}}}
\lstdefinelanguage{CSS}{sensitive=true,morecomment=[s]{/*}{*/},morestring=[b]",morestring=[b]',alsoletter={-},morekeywords={align-items,background,background-color,border,border-radius,box-shadow,box-sizing,color,display,flex,font-family,font-size,font-weight,gap,grid-template-columns,height,justify-content,margin,max-width,min-height,padding,position,transition,width,@media,important,auto,block,grid,none,relative,absolute,center,solid,rem,px,white,black}}
\lstdefinelanguage{JavaScript}{sensitive=true,morecomment=[l]{//},morecomment=[s]{/*}{*/},morestring=[b]",morestring=[b]',morekeywords={const,let,var,function,return,if,else,for,while,break,continue,class,new,this,throw,try,catch,finally,async,await,import,from,export,default,true,false,null,undefined,typeof,instanceof,console,log,document,window,addEventListener,querySelector,querySelectorAll,getElementById,Math,Number,String,Array,Object,Promise,fetch}}
\lstdefinelanguage{Python}{sensitive=true,morecomment=[l]{\#},morestring=[b]',morestring=[b]",morekeywords={and,as,assert,break,class,continue,def,del,elif,else,except,False,finally,for,from,global,if,import,in,is,lambda,None,not,or,pass,raise,return,True,try,while,with,yield,print,input,range,len,type,int,float,str,list,dict,tuple,set}}
\lstdefinelanguage{Pseudo}{morekeywords={START,STOP,INPUT,OUTPUT,IF,THEN,ELSE,ENDIF,WHILE,DO,ENDWHILE,FOR,ENDFOR},sensitive=false}
\lstdefinelanguage{PHP}{sensitive=true,morecomment=[l]{//},morecomment=[s]{/*}{*/},morestring=[b]',morestring=[b]",morekeywords={echo,print,if,else,elseif,while,for,foreach,function,return,include,require,isset,empty,global,new,try,catch,throw,public,private,protected,class,true,false,null}}
\lstdefinelanguage{SQL}{morekeywords={SELECT,FROM,WHERE,ORDER,BY,GROUP,INSERT,INTO,VALUES,UPDATE,SET,DELETE,CREATE,DATABASE,TABLE,ALTER,DROP,PRIMARY,KEY,FOREIGN,REFERENCES,NOT,NULL,UNIQUE,DEFAULT,JOIN,LEFT,INNER,ON,AS,COUNT,SUM,AVG,MIN,MAX,GRANT,REVOKE,COMMIT,ROLLBACK,USE,INT,VARCHAR,TINYINT,CHECK,HAVING,RIGHT,AND,OR,IS,IN,LIKE,LIMIT},sensitive=false,morecomment=[l]{--},morestring=[b]'}
\newcommand{\review}[1]{\par\smallskip\reviewtitle\begin{enumerate}[label=\arabic*.,leftmargin=1.8em,itemsep=1pt,topsep=2pt]\small #1\end{enumerate}\smallskip}
\lstdefinestyle{webcode}{basicstyle=\ttfamily\small,keywordstyle=\color{Navy}\bfseries,commentstyle=\color{Teal},stringstyle=\color{Violet},numbers=left,numberstyle=\tiny\color{Ink!65},stepnumber=1,numbersep=8pt,showstringspaces=false,breaklines=true,frame=single,rulecolor=\color{Teal!55},backgroundcolor=\color{SoftGray},xleftmargin=2mm,framexleftmargin=2mm,aboveskip=5pt,belowskip=5pt}
\lstset{style=webcode}
% Prevent LaTeX's alphabetic Appendix numbering from overflowing after Appendix Z.
\renewcommand{\appendixname}{Appendix}
\renewcommand{\thechapter}{\arabic{chapter}}
\makeatletter\renewcommand{\@chapapp}{\chaptername}\makeatother
"""
    cover = r"""\begin{document}
\begin{titlepage}\thispagestyle{empty}
\begin{tikzpicture}[remember picture,overlay]
\fill[Navy] (current page.north west) rectangle ([yshift=-10cm]current page.north east);
\fill[Teal] ([yshift=-10cm]current page.north west) rectangle ([yshift=-10.28cm]current page.north east);
\fill[Coral] ([yshift=-10.28cm]current page.north west) rectangle ([yshift=-10.42cm]current page.north east);
\draw[Gold,line width=2pt] ([xshift=22mm,yshift=-20mm]current page.north west)--([xshift=-22mm,yshift=-20mm]current page.north east);
\draw[Gold,line width=1pt] ([xshift=22mm,yshift=-90mm]current page.north west)--([xshift=-22mm,yshift=-90mm]current page.north east);
\end{tikzpicture}
\vspace*{19mm}
{\color{white}\rmfamily\bfseries\fontsize{42}{48}\selectfont HANDBOOK\par}
\vspace{6mm}{\color{Gold}\rule{.72\textwidth}{1.2pt}\par}
\vspace{10mm}{\color{white}\sffamily\LARGE Combined Vocational Education Textbooks\par}
\vspace{4mm}{\color{white}\sffamily\large Classes IX–XII\par}
\vfill
\begin{center}{\sffamily\Large\bfseries\color{Teal} Data Entry \textbullet\ Web Development \textbullet\ Artificial Intelligence \textbullet\ Software Development\par}\end{center}
\vfill
\begin{center}{\small A combined learning handbook\par}\end{center}
\end{titlepage}
\frontmatter
\tableofcontents
\mainmatter
"""
    output = ROOT / "Final Book" / "main.tex"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(preamble + "\n" + cover + "\n\n".join(sections) + "\n\\end{document}\n", encoding="utf-8")
    print(f"Generated {output} from {len(BOOKS)} source books.")

if __name__ == "__main__":
    main()
