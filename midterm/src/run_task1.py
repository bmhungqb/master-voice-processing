"""
Task 1 Pipeline Runner: Text Extraction, Cleaning, DTBook XML Generation & Validation.
Book: Trong Gia Đình (Hector Malot)
"""

import os
import sys
import json
import argparse
from typing import List

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import EPUB_PATH, OUTPUT_DIR, METADATA, TOTAL_CHAPTERS
from src.extract_clean import extract_chapter
from src.generate_dtbook import save_dtbook_file
from src.validate_dtbook import validate_dtbook_file


def process_chapter(chapter_idx: int, epub_path: str = EPUB_PATH, base_output_dir: str = OUTPUT_DIR) -> dict:
    """
    Process a single chapter: extract, generate DTBook XML, save segments.json, and validate.
    """
    if chapter_idx == 0:
        chapter_folder_name = "Trong_Gia_Dinh-Gioi_Thieu"
    else:
        chapter_folder_name = f"Trong_Gia_Dinh-Chuong_{chapter_idx:02d}"
    chapter_dir = os.path.join(base_output_dir, chapter_folder_name)
    os.makedirs(chapter_dir, exist_ok=True)

    dtbook_xml_path = os.path.join(chapter_dir, "dtbook.xml")
    segments_json_path = os.path.join(chapter_dir, "segments.json")

    # 1. Extract and clean chapter text
    chapter_data = extract_chapter(epub_path, chapter_idx)

    # 2. Save DTBook XML
    save_dtbook_file(chapter_data, dtbook_xml_path, METADATA)

    # 3. Save handoff segments.json for TTS (Member 2) and Alignment (Member 3)
    handoff_data = {
        "metadata": METADATA,
        "chapter_idx": chapter_idx,
        "chapter_title": chapter_data["chapter_title"],
        "total_paragraphs": chapter_data["total_paragraphs"],
        "total_sentences": chapter_data["total_sentences"],
        "segments": chapter_data["flat_segments"]
    }
    with open(segments_json_path, "w", encoding="utf-8") as f:
        json.dump(handoff_data, f, ensure_ascii=False, indent=2)

    # 4. Validate DTBook XML
    is_valid, errors, stats = validate_dtbook_file(dtbook_xml_path)

    return {
        "chapter_idx": chapter_idx,
        "chapter_title": chapter_data["chapter_title"],
        "paragraphs": chapter_data["total_paragraphs"],
        "sentences": chapter_data["total_sentences"],
        "valid": is_valid,
        "errors": errors,
        "xml_path": dtbook_xml_path,
        "json_path": segments_json_path,
        "stats": stats
    }


def run_pipeline(chapter_indices: List[int], epub_path: str = EPUB_PATH, output_dir: str = OUTPUT_DIR):
    print("=" * 70)
    print("  TASK 1: TEXT & XML PIPELINE - 'TRONG GIA ĐÌNH' (DAISY 3 / DTBOOK)")
    print(f"  ISBN: {METADATA['dc:Identifier']} | NXB: {METADATA['dc:Publisher']}")
    print("=" * 70)

    results = []
    for idx in chapter_indices:
        print(f"[*] Processing Chapter {idx:02d}...", end=" ", flush=True)
        res = process_chapter(idx, epub_path, output_dir)
        if res["valid"]:
            print(f"✅ OK ({res['paragraphs']} paras, {res['sentences']} sents)")
        else:
            print(f"❌ INVALID ({len(res['errors'])} errors)")
            for err in res["errors"]:
                print(f"    - {err}")
        results.append(res)

    print("\n" + "=" * 70)
    print("  SUMMARY REPORT")
    print("=" * 70)
    print(f"{'Ch':<4} | {'Title':<36} | {'Paras':<6} | {'Sents':<6} | {'Status'}")
    print("-" * 70)

    total_paras = 0
    total_sents = 0
    all_valid = True

    for r in results:
        title = r["chapter_title"]
        if len(title) > 34:
            title = title[:31] + "..."
        status = "PASSED" if r["valid"] else "FAILED"
        print(f"{r['chapter_idx']:<4} | {title:<36} | {r['paragraphs']:<6} | {r['sentences']:<6} | {status}")
        total_paras += r["paragraphs"]
        total_sents += r["sentences"]
        if not r["valid"]:
            all_valid = False

    print("-" * 70)
    print(f"TOTAL: {len(results)} chapters | {total_paras} paragraphs | {total_sents} sentences")
    print(f"ALL FILES VALID: {'✅ YES' if all_valid else '❌ NO'}")
    print(f"Output Directory: {output_dir}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Task 1: Process EPUB to DAISY 3 DTBook XML")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pilot", action="store_true", help="Run pilot on Chapter 0 & Chapter 1")
    group.add_argument("--all", action="store_true", help="Process all 23 chapters (C0 to C22)")
    group.add_argument("--chapter", type=int, help="Process a specific chapter index (0-22)")

    args = parser.parse_args()

    if args.pilot:
        targets = [0, 1]
    elif args.all:
        targets = list(range(TOTAL_CHAPTERS))
    else:
        targets = [args.chapter]

    run_pipeline(targets)


if __name__ == "__main__":
    main()
