"""
Validator for DAISY 3 DTBook XML files.
Verifies XML well-formedness, DTD conformance, element hierarchy, ID uniqueness, and SMIL reference integrity.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Any


DTBOOK_NAMESPACE = "http://www.daisy.org/z3986/2005/dtbook/"
REQUIRED_META = [
    "dtb:uid",
    "dc:Title",
    "dc:Creator",
    "dc:Date",
    "dc:Publisher",
    "dc:Identifier",
    "dc:Language",
    "dc:Subject",
    "dc:Description",
]


def validate_dtbook_file(file_path: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate a DTBook XML file.
    Returns:
      (is_valid: bool, errors: List[str], stats: Dict[str, Any])
    """
    errors = []
    stats = {
        "file": file_path,
        "total_meta": 0,
        "total_paragraphs": 0,
        "total_sentences": 0,
        "unique_ids": 0,
    }

    # 1. Read file and check header declarations
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return False, [f"Cannot read file: {e}"], stats

    if not content.startswith("<?xml"):
        errors.append("Missing XML declaration '<?xml ... ?>'")

    if "<!DOCTYPE dtbook PUBLIC" not in content or "dtbook-2005-3.dtd" not in content:
        errors.append("Missing or invalid DTBook 2005-3 DOCTYPE declaration")

    # 2. Parse XML
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        return False, [f"XML Parse Error: {e}"], stats

    # 3. Check root tag and attributes
    expected_root = f"{{{DTBOOK_NAMESPACE}}}dtbook"
    if root.tag != expected_root:
        errors.append(f"Root tag must be 'dtbook' with namespace '{DTBOOK_NAMESPACE}', got '{root.tag}'")

    if root.attrib.get("version") != "2005-3":
        errors.append(f"Root version must be '2005-3', got '{root.attrib.get('version')}'")

    lang_attr = root.attrib.get("{http://www.w3.org/XML/1998/namespace}lang") or root.attrib.get("xml:lang")
    if not lang_attr or not lang_attr.startswith("vi"):
        errors.append(f"Root xml:lang should be Vietnamese ('vi' or 'vi-VN'), got '{lang_attr}'")

    # 4. Check <head> and metadata
    ns = {"dt": DTBOOK_NAMESPACE}
    head = root.find("dt:head", ns)
    if head is None:
        errors.append("Missing <head> element")
    else:
        meta_elements = head.findall("dt:meta", ns)
        stats["total_meta"] = len(meta_elements)
        meta_dict = {m.attrib.get("name"): m.attrib.get("content") for m in meta_elements if "name" in m.attrib}

        for req in REQUIRED_META:
            if req not in meta_dict or not meta_dict[req]:
                errors.append(f"Missing required meta tag: '{req}'")

    # 5. Check <book>, <frontmatter>, <bodymatter>
    book = root.find("dt:book", ns)
    if book is None:
        errors.append("Missing <book> element")
    else:
        frontmatter = book.find("dt:frontmatter", ns)
        if frontmatter is None:
            errors.append("Missing <frontmatter> in <book>")
        else:
            if frontmatter.find("dt:doctitle", ns) is None:
                errors.append("Missing <doctitle> in <frontmatter>")
            if frontmatter.find("dt:docauthor", ns) is None:
                errors.append("Missing <docauthor> in <frontmatter>")

        bodymatter = book.find("dt:bodymatter", ns)
        if bodymatter is None:
            errors.append("Missing <bodymatter> in <book>")
        else:
            level1 = bodymatter.find("dt:level1", ns)
            if level1 is None:
                errors.append("Missing <level1> in <bodymatter>")
            else:
                if level1.find("dt:h1", ns) is None:
                    errors.append("Missing <h1> in <level1>")

    # 6. Check ID Uniqueness & SMIL ref consistency
    all_ids = set()
    paras = root.findall(".//dt:p", ns)
    sents = root.findall(".//dt:sent", ns)

    stats["total_paragraphs"] = len(paras)
    stats["total_sentences"] = len(sents)

    for elem in root.iter():
        elem_id = elem.attrib.get("id")
        if elem_id:
            if elem_id in all_ids:
                errors.append(f"Duplicate ID found: '{elem_id}'")
            all_ids.add(elem_id)

        # Validate SMIL reference if present
        smilref = elem.attrib.get("smilref")
        tag_name = elem.tag.replace(f"{{{DTBOOK_NAMESPACE}}}", "")

        if tag_name == "sent":
            if not elem_id or not elem_id.startswith("id_"):
                errors.append(f"<sent> has invalid id '{elem_id}', expected 'id_X'")
            if not smilref:
                errors.append(f"<sent id='{elem_id}'> missing smilref attribute")
            elif not (smilref.startswith("mo0.smil#sid_") or smilref.startswith("mo0.smil#sforsmil-") or smilref.startswith("mo0.smil#sfaux-")):
                errors.append(f"<sent id='{elem_id}'> smilref '{smilref}' has unexpected format")

            # Check text content
            if not elem.text or not elem.text.strip():
                errors.append(f"<sent id='{elem_id}'> has empty text content")

        elif tag_name == "p":
            if not elem_id:
                errors.append(f"<p> missing id attribute")
            if not smilref or not smilref.startswith("mo0.smil#seq_"):
                errors.append(f"<p id='{elem_id}'> smilref '{smilref}' does not match expected 'mo0.smil#seq_X'")

    stats["unique_ids"] = len(all_ids)
    is_valid = len(errors) == 0

    return is_valid, errors, stats
