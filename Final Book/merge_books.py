from __future__ import annotations

import argparse
import re
import json
import urllib.parse
import urllib.request
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
    # Strip all source-level page styles/marks so no original book headers or footers leak into the combined volume.
    text = re.sub(r"\\thispagestyle\{[^}]*\}|\\pagestyle\{[^}]*\}", "", text)
    text = re.sub(r"\\markboth\{[^{}]*\}\{[^{}]*\}|\\markright\{[^{}]*\}", "", text)
    text = re.sub(r"\\fancy(?:head|foot)\s*(?:\[[^]]*\])?\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", "", text)
    # Rewrite every source-book asset path (including \IfFileExists guards) to the
    # copied, space-free assets/bookN tree. This prevents false "illustration unavailable"
    # messages when the image exists in the repository/build workspace.
    book_index = next(i for i, item in enumerate(BOOKS, start=1) if item.folder == path.parent.name)
    source_prefix = re.escape("../" + path.parent.name + "/")
    text = re.sub(source_prefix, f"assets/book{book_index}/", text)
    # Source books also use paths relative to their own folder. Redirect these too.\n    text = re.sub(r"(?<![A-Za-z0-9_./-])(images|book_illustrations)/", rf"assets/book{book_index}/\\g<1>/", text)\n    # Keep photos and diagrams inside the page's vertical text area to prevent overlap.
    def constrain_image(match: re.Match[str]) -> str:
        options = match.group(1) or ""
        image_path = match.group(2)
        if not re.search(r"\bheight\s*=", options):
            options = options.strip("[]")
            options = (options + "," if options else "") + r"height=55mm,keepaspectratio"
            options = "[" + options + "]"
        return r"\includegraphics" + options + "{" + image_path + "}"
    text = re.sub(r"\\includegraphics(\[[^\]]*\])?\{([^{}]+)\}", constrain_image, text)
    # Missing optional source illustrations must not abort the entire textbook build.
    # Keep every valid image; show a small fallback only when a referenced file is absent.
    def guard_image(match: re.Match[str]) -> str:
        options = match.group(1) or ""
        image_path = match.group(2)
        original = f"\\includegraphics{options}{{{image_path}}}"
        return f"\\IfFileExists{{{image_path}}}{{{original}}}{{\\relax}}"
    text = re.sub(r"\\includegraphics(\[[^\]]*\])?\{([^{}]+)\}", guard_image, text)
    # Older source books may use raw LaTeX \input{...} or \include{...}; keep these
    # untouched unless those files exist in the merged directory, to avoid fatal missing-file errors.
    text = re.sub(r"\\input\{([^{}]+)\}", lambda m: m.group(0) if (FINAL_BOOK_DIR / m.group(1)).exists() else "% omitted missing input " + m.group(1), text)
    text = re.sub(r"\\include\{([^{}]+)\}", lambda m: m.group(0) if (FINAL_BOOK_DIR / (m.group(1) + ".tex")).exists() else "% omitted missing include " + m.group(1), text)
    # Normalise code listings from independently authored curricula. Unknown source styles
    # and language names can stop XeLaTeX; preserve code and general options, use plain code layout.
    def normalise_listing(match: re.Match[str]) -> str:
        options = match.group(1)
        kept = []
        for item in options.split(","):
            item = item.strip()
            if re.match(r"^(style|language)\s*=", item, flags=re.I):
                continue
            if item:
                kept.append(item)
        return r"\begin{lstlisting}" + ("[" + ",".join(kept) + "]" if kept else "")
    text = re.sub(r"\\begin\{lstlisting\}\[([^\]]*)\]", normalise_listing, text, flags=re.I)
    # Inline listings use the same safe fallback.
    text = re.sub(r"\\lstinline(?:\[[^\]]*\])?", r"\\lstinline", text)
    # The book parts are stitched together without creating separate books or cover pages.
    return text.strip()

_USED_SECTION_IMAGES: set[str] = set()
_USED_COMMONS_TITLES: set[str] = set()

def _fetch_web_image(title: str, book_index: int, context: str = "") -> str | None:
    """Find a unique, topic-matched image via Openverse, then Bing Images."""
    title_clean = re.sub(r"[^A-Za-z0-9 ]+", " ", title).strip()
    if not title_clean:
        return None
    # Use the section's actual content to disambiguate vague headings such as
    # "Procedure", "Observation prompts", or "Introduction".
    body_text = re.sub(r"\\\\[A-Za-z]+(?:\\[[^]]*\\])?(?:\\{[^{}]*\\})?", " ", context)
    body_words = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", body_text)]
    stop = {"this","that","with","from","they","their","should","would","could","have","will","when","where","which","what","into","about","using","used","each","more","than","then","also","section","learners","students","topic","must","make","made","ensure","explain","describe","practice","practise","activity","procedure","prompts"}
    keywords = []
    for word in body_words:
        if word not in stop and word not in keywords:
            keywords.append(word)
        if len(keywords) >= 8:
            break
    query = " ".join([title_clean] + keywords[:5])
    destination_dir = FINAL_BOOK_DIR / "assets" / f"book{book_index}" / "section_images"
    destination_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", title_clean.lower()).strip("-")[:54] or "topic"
    headers = {"User-Agent": "SAI-Vocational-Textbook-Builder/1.0 (topic image search)"}

    # Prefer a licensed-image index with descriptive titles and source metadata.
    try:
        api = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({
            "q": query + " person working", "page_size": 40, "license": "cc0,by,by-sa,pdm", "category": "photograph", "size": "large", "aspect_ratio": "wide"
        })
        req = urllib.request.Request(api, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        title_terms = set(re.findall(r"[a-z]{3,}", title_clean.lower())) | set(keywords[:8])
        candidates = []
        for item in payload.get("results", []):
            result_title = (item.get("title") or "").lower()
            result_tags = " ".join(tag.get("name", "") for tag in item.get("tags", []) if isinstance(tag, dict)).lower()
            combined = result_title + " " + result_tags
            score = sum(4 for word in set(re.findall(r"[a-z]{3,}", title_clean.lower())) if word in combined)
            score += sum(2 for word in keywords[:8] if word in combined)
            if any(term in combined for term in ("person", "people", "student", "teacher", "worker", "computer", "office", "classroom", "workplace", "hands")):
                score += 2
            url = item.get("url") or item.get("thumbnail")
            if url and item.get("id") not in _USED_COMMONS_TITLES:
                candidates.append((score, item, url))
        candidates.sort(key=lambda row: (-row[0], (row[1].get("title") or "").lower()))
        for score, item, url in candidates:
            # Avoid weak matches; never use a generic image just to fill the page.
            if score < 4:
                continue
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as response:
                    data = response.read()
                    content_type = response.headers.get("Content-Type", "").lower()
                if len(data) < 8000 or not content_type.startswith("image/"):
                    continue
                ext = ".png" if "png" in content_type else ".webp" if "webp" in content_type else ".jpg"
                filename = f"openverse-{slug}-{len(_USED_SECTION_IMAGES)+1}{ext}"
                destination = destination_dir / filename
                destination.write_bytes(data)
                rel = destination.relative_to(FINAL_BOOK_DIR).as_posix()
                _USED_SECTION_IMAGES.add(rel)
                _USED_SECTION_IMAGES.add(destination.name.lower())
                _USED_COMMONS_TITLES.add(item.get("id", ""))
                print(f"Openverse match for {title!r}: {item.get('title')} | license={item.get('license')} | source={item.get('foreign_landing_url')}")
                return rel
            except Exception:
                continue
    except Exception as exc:
        print(f"Openverse image search skipped for {title!r}: {exc}")

    # Secondary web search: use the detailed query rather than the heading alone.
    search_url = "https://www.bing.com/images/search?" + urllib.parse.urlencode({"q": query + " educational"})
    try:
        req = urllib.request.Request(search_url, headers={"User-Agent": "Mozilla/5.0 (compatible; SAITextbookBuilder/1.0)"})
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode("utf-8", errors="ignore")
        candidates = []
        for raw in re.findall(r'"murl":"(https?://[^"]+)"', html, flags=re.I):
            url = raw.replace(r"\\u0026", "&").replace(r"\\/", "/").replace("&amp;", "&")
            if url.startswith("https://") and not any(x in url.lower() for x in ("bing.com/th", "bing.com/")):
                candidates.append(url)
        for url in candidates[:20]:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = response.read()
                    content_type = response.headers.get("Content-Type", "").lower()
                if len(data) < 12000 or not content_type.startswith("image/"):
                    continue
                ext = ".png" if "png" in content_type else ".webp" if "webp" in content_type else ".jpg"
                destination = destination_dir / f"bing-{slug}-{len(_USED_SECTION_IMAGES)+1}{ext}"
                destination.write_bytes(data)
                rel = destination.relative_to(FINAL_BOOK_DIR).as_posix()
                _USED_SECTION_IMAGES.add(rel)
                _USED_SECTION_IMAGES.add(destination.name.lower())
                print(f"Bing image candidate fetched for {title!r}; verify source/license: {url}")
                return rel
            except Exception:
                continue
    except Exception as exc:
        print(f"Bing image search skipped for {title!r}: {exc}")
    return None

def _fetch_unique_commons_image(title: str, book_index: int) -> str | None:
    """Search Wikimedia Commons for a relevant reusable image and download it once."""
    query = re.sub(r"[^A-Za-z0-9 ]+", " ", title).strip()
    if not query:
        return None
    destination_dir = FINAL_BOOK_DIR / "assets" / f"book{book_index}" / "section_images"
    destination_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:54] or "topic"
    api = "https://commons.wikimedia.org/w/api.php?"
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": f'filetype:bitmap "{query}"',
        "gsrnamespace": "6", "gsrlimit": "12",
        "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": "1200", "format": "json"
    }
    try:
        request = urllib.request.Request(
            api + urllib.parse.urlencode(params),
            headers={"User-Agent": "BooksEducationalTextbookBuilder/1.0 (image attribution included)"}
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
        pages = payload.get("query", {}).get("pages", {})
        candidates = sorted(pages.values(), key=lambda page: page.get("title", "").lower())
        # Prefer the search order returned by Commons by sorting on index when available.
        candidates.sort(key=lambda page: page.get("index", 999))
        for page in candidates:
            file_title = page.get("title", "")
            infos = page.get("imageinfo", [])
            if not infos or file_title in _USED_COMMONS_TITLES:
                continue
            info = infos[0]
            url = info.get("thumburl") or info.get("url", "")
            ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            if not url:
                continue
            filename = f"{slug}-{len(_USED_SECTION_IMAGES)+1}{ext}"
            destination = destination_dir / filename
            req = urllib.request.Request(url, headers={"User-Agent": "BooksEducationalTextbookBuilder/1.0"})
            with urllib.request.urlopen(req, timeout=18) as response:
                data = response.read()
            if len(data) < 5000:
                continue
            destination.write_bytes(data)
            _USED_COMMONS_TITLES.add(file_title)
            _USED_SECTION_IMAGES.add(destination.relative_to(FINAL_BOOK_DIR).as_posix())
            _USED_SECTION_IMAGES.add(file_title)
            return destination.relative_to(FINAL_BOOK_DIR).as_posix()
    except Exception as exc:
        print(f"Commons image search skipped for {title!r}: {exc}")
    return None

def _generate_topic_image(title: str, book_index: int) -> str:
    """Create a distinct topic illustration locally during GitHub Actions when web search fails."""
    from PIL import Image, ImageDraw, ImageFont
    output_dir = FINAL_BOOK_DIR / "assets" / f"book{book_index}" / "section_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "topic"
    serial = len(_USED_SECTION_IMAGES) + 1
    output = output_dir / f"generated-{serial:04d}-{slug}.png"
    width, height = 1200, 620
    image = Image.new("RGB", (width, height), "#f4f7fb")
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 38)
        label_font = ImageFont.truetype("DejaVuSans.ttf", 24)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 19)
    except OSError:
        title_font = label_font = small_font = ImageFont.load_default()
    draw.rounded_rectangle((28, 28, width-28, height-28), radius=28, fill="white", outline="#176b78", width=5)
    draw.rounded_rectangle((52, 52, width-52, 145), radius=20, fill="#17365d")
    display_title = title if len(title) <= 54 else title[:51] + "..."
    draw.text((78, 78), display_title, font=title_font, fill="white")
    words = set(re.findall(r"[a-z]+", title.lower()))
    if words & {"database","sql","query","table","record","spreadsheet","data"}:
        labels = ["Input records", "Validate data", "Store securely", "Retrieve results"]
        symbols = ["01", "02", "03", "04"]
    elif words & {"html","css","javascript","web","website","php","browser"}:
        labels = ["Structure", "Style", "Interaction", "Web page"]
        symbols = ["<>", "{ }", "JS", "WWW"]
    elif words & {"network","router","lan","internet","server","cloud"}:
        labels = ["Device", "Connection", "Server", "Network"]
        symbols = ["PC", "↔", "SV", "NET"]
    elif words & {"artificial","intelligence","machine","learning","model","robot","assistant"}:
        labels = ["Collect data", "Learn patterns", "Test model", "Use results"]
        symbols = ["DATA", "AI", "TEST", "OUT"]
    elif words & {"safety","health","emergency","fire","workstation","ergonomic"}:
        labels = ["Identify risk", "Assess area", "Take action", "Check safety"]
        symbols = ["!", "02", "✓", "SAFE"]
    elif words & {"software","program","python","algorithm","code","system","process"}:
        labels = ["Plan", "Write code", "Test", "Improve"]
        symbols = ["PLAN", "</>", "TEST", "✓"]
    else:
        labels = ["Understand", "Organise", "Apply", "Review"]
        symbols = ["01", "02", "03", "04"]
    colors = ["#dceeff", "#dff4ee", "#fff0d2", "#f0e7ff"]
    lefts = [70, 350, 630, 910]
    for i, (x, label, symbol) in enumerate(zip(lefts, labels, symbols)):
        draw.rounded_rectangle((x, 220, x+220, 445), radius=22, fill=colors[i], outline="#9aabba", width=3)
        draw.ellipse((x+64, 245, x+156, 337), fill="#17365d")
        bbox = draw.textbbox((0, 0), symbol, font=label_font)
        sw, sh = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text((x+110-sw/2, 291-sh/2), symbol, font=label_font, fill="white")
        bbox = draw.textbbox((0, 0), label, font=label_font)
        draw.text((x+110-(bbox[2]-bbox[0])/2, 365), label, font=label_font, fill="#17365d")
        if i < 3:
            draw.line((x+224, 330, x+270, 330), fill="#176b78", width=6)
            draw.polygon([(x+270,330),(x+254,319),(x+254,341)], fill="#176b78")
    draw.text((72, 500), "Topic illustration • Created locally during the repository build", font=small_font, fill="#526579")
    image.save(output, format="PNG", optimize=True)
    rel = output.relative_to(FINAL_BOOK_DIR).as_posix()
    _USED_SECTION_IMAGES.add(rel)
    _USED_SECTION_IMAGES.add(output.name.lower())
    return rel

def add_section_illustrations(text: str, book_index: int) -> str:
    """Give each section its own topic-relevant image; never reuse an image in a later section."""
    pattern = re.compile(r"(\\section\*?\{[^{}]*\})(.*?)(?=\\(?:section\*?|chapter\*?|part\*?)\{|\\appendix\b|$)", re.S)
    def update(match: re.Match[str]) -> str:
        heading, body = match.group(1), match.group(2)
        existing = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^{}]+)\}", body)
        for image_path in existing:
            full = FINAL_BOOK_DIR / image_path
            if full.is_file():
                key = full.resolve().as_posix()
                if key not in _USED_SECTION_IMAGES:
                    _USED_SECTION_IMAGES.add(key)
                    _USED_SECTION_IMAGES.add(full.name.lower())
                    return heading + body
        title = re.sub(r"\\section\*?\{|\}", "", heading).strip()
        web_path = _fetch_web_image(title, book_index, body)
        commons_path = web_path or _fetch_unique_commons_image(title, book_index)
        if commons_path:
            image_path = commons_path
        else:
            # Fall back to a previously committed, unused topic-specific image.
            words = set(re.findall(r"[a-z]+", title.lower()))
            assets = []
            for folder in sorted((FINAL_BOOK_DIR / "assets").glob("book*")):
                for subdir in ("images", "book_illustrations"):
                    directory = folder / subdir
                    if directory.is_dir():
                        for path in directory.rglob("*"):
                            if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                                continue
                            if path.name.lower().startswith("human-") or path.name.lower() == "people-photo.jpg":
                                continue
                            rel = path.relative_to(FINAL_BOOK_DIR).as_posix()
                            if rel in _USED_SECTION_IMAGES or path.name.lower() in _USED_SECTION_IMAGES:
                                continue
                            score = sum(1 for word in words if len(word) > 3 and word in path.name.lower())
                            if score:
                                assets.append((score, rel, path))
            if not assets:
                # Never insert generic generated diagrams. If web search and committed
                # topic-matched assets fail, leave this section without an image.
                print(f"No suitable non-repeating web/local image found for section: {title}")
                return heading + body
            else:
                assets.sort(key=lambda item: (-item[0], item[1]))
                _, image_path, chosen = assets[0]
                _USED_SECTION_IMAGES.add(image_path)
                _USED_SECTION_IMAGES.add(chosen.name.lower())
        image = (
            "\n\\begin{center}\\vspace{-2pt}"
            "\\includegraphics[width=.72\\textwidth,height=38mm,keepaspectratio]{"
            + image_path + "}"
            "\\end{center}\n"
        )
        return heading + image + body
    return pattern.sub(update, text)

def render_main_tex(tex_path: Path) -> str:
    bodies = []
    for index, book in enumerate(BOOKS, start=1):
        path = source_tex(book)
        body = extract_body(path)
        body = add_section_illustrations(body, index)
        # Topic-matched section images are inserted once each; do not add repeated curriculum-opening photos.
        # Keep the source chapter text and illustrations; only mark transitions between source curricula.
        bodies.append(
            "\n% ============================================================\n"
            f"% Curriculum sequence {index}: {book.title}\n"
            "% ============================================================\n"
            + body
        )

    body_text = "\n\n".join(bodies)
    return r"""\documentclass[11pt,openany,oneside]{book}
\usepackage[a4paper,top=25mm,bottom=25mm,left=25mm,right=22mm,headheight=22pt,footskip=14mm]{geometry}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\usepackage{amssymb,xcolor,graphicx,array,booktabs,longtable,tabularx,colortbl,enumitem,tikz,tcolorbox,fancyhdr,titlesec,tocloft,hyperref,eso-pic,microtype,listings}
\lstdefinestyle{webcode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{pythoncode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{pythonstyle}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{sqlcode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{htmlcode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{csscode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{js code}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{code}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{bashcode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{javacode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{jsoncode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{phpcode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{typescriptcode}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{sqlstyle}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinestyle{terminal}{basicstyle=\ttfamily\small,breaklines=true,showstringspaces=false,columns=fullflexible,frame=single}
\lstdefinelanguage{HTML}{sensitive=false,morecomment=[s]{<!--}{-->},morestring=[b]",morestring=[b]',morekeywords={html,head,title,body,div,span,p,h1,h2,h3,a,img,ul,ol,li,table,tr,td,th,form,input,button,script,style,meta,link,header,footer,section,article,nav,main}}
\lstdefinelanguage{CSS}{sensitive=false,morecomment=[s]{/*}{*/},morestring=[b]",morestring=[b]',morekeywords={color,background,display,position,margin,padding,border,width,height,font,font-size,font-family,flex,grid,justify-content,align-items,content,selector,px,rem,em,none,block,inline,solid,relative,absolute,hover,media}}
\lstdefinelanguage{JavaScript}{sensitive=false,morecomment=[l]{//},morecomment=[s]{/*}{*/},morestring=[b]",morestring=[b]',morekeywords={const,let,var,function,return,if,else,for,while,class,new,import,export,from,async,await,document,window,console,log,true,false,null,undefined}}
\lstdefinelanguage{JSON}{sensitive=false,morestring=[b]",morekeywords={true,false,null}}
\lstdefinelanguage{bash}{sensitive=false,morecomment=[l]{\#},morestring=[b]",morestring=[b]',morekeywords={cd,ls,echo,export,git,npm,node,python,pip,mkdir,cp,mv,rm,sudo,apt}}
\lstdefinelanguage{Java}{sensitive=false,morecomment=[l]{//},morecomment=[s]{/*}{*/},morestring=[b]",morekeywords={public,private,protected,class,static,void,int,double,float,boolean,String,return,new,if,else,for,while,try,catch,import,package,extends,implements}}
\lstdefinelanguage{PHP}{sensitive=false,morecomment=[l]{//},morecomment=[s]{/*}{*/},morestring=[b]",morestring=[b]',morekeywords={echo,print,function,return,if,else,foreach,while,for,class,public,private,protected,new,include,require,isset,empty}}
\lstdefinelanguage{TypeScript}{sensitive=false,morecomment=[l]{//},morecomment=[s]{/*}{*/},morestring=[b]",morestring=[b]',morekeywords={const,let,var,function,return,if,else,for,while,class,interface,type,import,export,from,async,await,true,false,null,undefined}}
\lstdefinelanguage{MongoDB}{sensitive=false,morecomment=[l]{//},morecomment=[s]{/*}{*/},morestring=[b]",morestring=[b]',morekeywords={db,find,insertOne,insertMany,updateOne,deleteOne,aggregate,createCollection,match,project,group,sort,limit}}
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
% Reserve enough room for three-digit chapter numbers in the single continuous contents list.
\setlength{\cftchapindent}{0em}
\setlength{\cftchapnumwidth}{4.2em}
\setlength{\cftsecindent}{1.8em}
\setlength{\cftsecnumwidth}{3.0em}
\setlength{\cftsubsecindent}{3.8em}
\setlength{\cftsubsecnumwidth}{3.6em}
\setlist[itemize]{leftmargin=1.5em,itemsep=1.5pt,topsep=2pt,parsep=0pt}
\setlist[enumerate]{leftmargin=1.7em,itemsep=2pt,topsep=2pt,parsep=0pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt}
\setlength{\emergencystretch}{3em}
% Consistent navy-teal-gold page border, running header, and continuous page number.
\AddToShipoutPictureBG{\begin{tikzpicture}[remember picture,overlay]
\draw[Navy,line width=1.15pt] ([xshift=9mm,yshift=-9mm]current page.north west) rectangle ([xshift=-9mm,yshift=9mm]current page.south east);
\draw[Teal,line width=.55pt] ([xshift=11.5mm,yshift=-11.5mm]current page.north west) rectangle ([xshift=-11.5mm,yshift=11.5mm]current page.south east);
\draw[Teal,line width=2pt] ([xshift=9mm,yshift=-9mm]current page.north west)--([xshift=35mm,yshift=-9mm]current page.north west);
\draw[Coral,line width=2pt] ([xshift=-9mm,yshift=9mm]current page.south east)--([xshift=-35mm,yshift=9mm]current page.south east);
\fill[Gold] ([xshift=9mm,yshift=-9mm]current page.north west) circle (1.2mm);
\fill[Violet] ([xshift=-9mm,yshift=9mm]current page.south east) circle (1.2mm);
\end{tikzpicture}}
\pagestyle{fancy}
\fancyhf{}
% No added running headers; keep only one continuous page number throughout the volume.
\fancyfoot[C]{\small\bfseries\color{Navy}\thepage}
\renewcommand{\headrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\small\bfseries\color{Navy}\thepage}\renewcommand{\headrulewidth}{0pt}}
\titleformat{\chapter}[display]{\normalfont\sffamily\bfseries\color{Navy}}{\filleft\Large\color{Coral}\chaptername\ \thechapter}{.6ex}{\color{Teal}\LARGE\raggedright}
\titlespacing*{\chapter}{0pt}{-2mm}{.8ex}
\titleformat{\section}{\Large\sffamily\bfseries\color{Teal}}{\color{Coral}\thesection}{.7em}{}
\titleformat{\subsection}{\large\sffamily\bfseries\color{Violet}}{\thesubsection}{.7em}{}
\titlespacing*{\section}{0pt}{1.2ex plus .2ex minus .2ex}{.35ex}
\titlespacing*{\subsection}{0pt}{1ex plus .2ex minus .2ex}{.3ex}
\newcommand{\keyterm}[1]{\textbf{\color{Navy}#1}}
\newcommand{\checklistitem}{\noindent$\square$\quad}
\newcommand{\exampractice}[1]{\begin{tcolorbox}[colback=LightGold,colframe=Gold,boxrule=.6pt,arc=1.2mm,left=2mm,right=2mm,top=1mm,bottom=1mm]\textbf{Review questions.} #1\end{tcolorbox}}
\newenvironment{keybox}{\begin{tcolorbox}[colback=Pale,colframe=Teal,boxrule=.6pt,arc=1mm,left=2mm,right=2mm,top=1mm,bottom=1mm]}{\end{tcolorbox}}
\newenvironment{notebox}{\begin{tcolorbox}[colback=SoftGray,colframe=Navy!70,boxrule=.6pt,arc=1mm,left=2mm,right=2mm,top=1mm,bottom=1mm]}{\end{tcolorbox}}
\newenvironment{examplebox}{\begin{tcolorbox}[colback=Sky!45,colframe=Teal!80,boxrule=.6pt,arc=1mm,left=2mm,right=2mm,top=1mm,bottom=1mm]}{\end{tcolorbox}}
\newenvironment{warningbox}{\begin{tcolorbox}[colback=Rose,colframe=Coral,boxrule=.6pt,arc=1mm,left=2mm,right=2mm,top=1mm,bottom=1mm]}{\end{tcolorbox}}
\newenvironment{activitybox}{\begin{tcolorbox}[colback=LightGold,colframe=Gold,boxrule=.6pt,arc=1mm,left=2mm,right=2mm,top=1mm,bottom=1mm]}{\end{tcolorbox}}
\newcommand{\reviewtitle}{\par\noindent\textbf{\color{Navy}Review Questions}\par}
\newcommand{\review}[1]{\par\smallskip\reviewtitle\begin{enumerate}[label=\arabic*.,leftmargin=1.8em,itemsep=1pt,topsep=2pt]\small #1\end{enumerate}\smallskip}
\newcommand{\photo}[3]{\begin{center}\begin{tcolorbox}[colback=white,colframe=Teal!70,boxrule=.8pt,arc=1mm,left=2mm,right=2mm,top=2mm,bottom=2mm,width=.88\textwidth]\centering\IfFileExists{../Junior software developer-11th/images/#1}{\includegraphics[width=.92\linewidth,height=46mm,keepaspectratio]{../Junior software developer-11th/images/#1}}{\textbf{#2}}\end{tcolorbox}\end{center}{\small\textit{#3}}}
\begin{document}
\pagenumbering{arabic}
\begin{titlepage}
\thispagestyle{plain}
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
