"""
Text extraction, cleaning, and sentence tokenization from EPUB.
Outputs clean structured segments per chapter.
"""

import re
import zipfile
from bs4 import BeautifulSoup
from typing import Dict, List, Any


# Common Vietnamese and French/English abbreviations to protect
ABBREVIATIONS = [
    "v.v", "gs", "nxb", "ts", "ths", "tp", "tt", "bt", "đ/c",
    "mr", "mrs", "dr", "ms", "etc", "i.e", "e.g", "tr"
]


def clean_text(raw_text: str) -> str:
    """Normalize whitespace and clean special characters."""
    if not raw_text:
        return ""
    # Replace non-breaking spaces
    text = raw_text.replace("\u00a0", " ").replace("&nbsp;", " ")
    # Normalize unicode whitespace
    text = re.sub(r"[\s\t\r\f\v]+", " ", text)
    # Standardize ellipsis
    text = text.replace("...", "…")
    return text.strip()


def split_sentences(text: str) -> List[str]:
    """
    Split Vietnamese text into sentences.
    Protects abbreviations, numbers, and dialogs.
    Avoids false splits after mid-sentence ellipsis when followed by lowercase.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    # Protect 'v.v…' or 'v.v.'
    protected = re.sub(r"\bv\.v[\.…]+", "v@DOT@v@ELLIP@", cleaned, flags=re.IGNORECASE)

    # Protect specific abbreviations ending with a dot
    for ab in ABBREVIATIONS:
        protected = re.sub(r"\b" + re.escape(ab) + r"\.", ab + "@DOT@", protected, flags=re.IGNORECASE)

    # Protect numbers with decimal points or dot separators (e.g. 10.000 or 3.14)
    protected = re.sub(r"(\d+)\.(\d+)", r"\1@DOT@\2", protected)

    # Sentence boundary: [.!?…] optionally followed by closing quotes or parentheses,
    # followed by whitespace and an uppercase letter / number / dialogue dash / quote,
    # or end of string.
    pattern = r"([.!?\u2026]+[\"\'”’»\)]*)(?=\s+[\"\'“‘«–—\-A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬĐÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴ0-9]|$)"

    raw_splits = re.split(pattern, protected)
    sentences = []
    i = 0
    while i < len(raw_splits):
        chunk = raw_splits[i].strip()
        if i + 1 < len(raw_splits):
            punct = raw_splits[i + 1].strip()
            full_sent = (chunk + punct).strip()
            i += 2
        else:
            full_sent = chunk
            i += 1

        if full_sent:
            # Restore protected characters
            full_sent = full_sent.replace("@DOT@", ".").replace("@ELLIP@", "…")
            sentences.append(full_sent)

    return sentences


# Manual overrides to correct typos in the original EPUB source
CHAPTER_TITLE_OVERRIDES = {
    0: "Giới Thiệu",
    5: "Phần II: Giã Từ Cõi Chết - Chương 5",
    22: "Chương 22",
}


def extract_chapter(epub_path: str, chapter_idx: int) -> Dict[str, Any]:
    """
    Extract a single chapter from the EPUB archive.
    Returns structured data with chapter title, paragraphs, and sentence segments.
    """
    html_filename = f"Text/C{chapter_idx}.html"

    with zipfile.ZipFile(epub_path, "r") as z:
        if html_filename not in z.namelist():
            raise FileNotFoundError(f"Chapter file {html_filename} not found in {epub_path}")

        raw_html = z.read(html_filename).decode("utf-8")

    soup = BeautifulSoup(raw_html, "html.parser")

    # Extract chapter title with typo correction
    if chapter_idx in CHAPTER_TITLE_OVERRIDES:
        chapter_title = CHAPTER_TITLE_OVERRIDES[chapter_idx]
    else:
        heading_tag = soup.find(["h1", "h2", "h3", "h4"])
        if heading_tag and heading_tag.get_text(strip=True):
            chapter_title = clean_text(heading_tag.get_text(strip=True))
        else:
            title_tag = soup.find("title")
            if title_tag and title_tag.get_text(strip=True):
                chapter_title = clean_text(title_tag.get_text(strip=True))
            else:
                chapter_title = f"Chương {chapter_idx}"

    # Extract paragraphs
    raw_paragraphs = []
    for p in soup.find_all("p"):
        txt = clean_text(p.get_text(strip=True))
        if txt:
            raw_paragraphs.append(txt)

    # Build structured representation with IDs matching DAISY 3 convention
    # id_1: doctitle
    # id_2: docauthor
    # id_3: chapter heading
    # id_4+: sentences in paragraphs
    sent_counter = 4
    para_counter = 1
    paragraphs_data = []
    flat_segments = []

    for p_text in raw_paragraphs:
        sents = split_sentences(p_text)
        if not sents:
            continue

        p_id = f"c{chapter_idx}_p{para_counter}"
        seq_id = f"seq_{para_counter}"

        p_entry = {
            "p_id": p_id,
            "seq_id": seq_id,
            "sentences": []
        }

        for s_text in sents:
            sent_id = f"id_{sent_counter}"
            smil_sid = f"sid_{sent_counter}"

            sent_entry = {
                "sent_id": sent_id,
                "smil_sid": smil_sid,
                "text": s_text
            }
            p_entry["sentences"].append(sent_entry)

            # Flat segment for TTS & Alignment handoff
            flat_segments.append({
                "sent_id": sent_id,
                "smil_sid": smil_sid,
                "p_id": p_id,
                "seq_id": seq_id,
                "text": s_text
            })

            sent_counter += 1

        paragraphs_data.append(p_entry)
        para_counter += 1

    return {
        "chapter_idx": chapter_idx,
        "chapter_title": chapter_title,
        "html_source": html_filename,
        "total_paragraphs": len(paragraphs_data),
        "total_sentences": len(flat_segments),
        "paragraphs": paragraphs_data,
        "flat_segments": flat_segments
    }
