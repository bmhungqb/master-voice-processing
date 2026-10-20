"""
Generate DAISY 3 compliant DTBook XML (DTBook 2005-3 / NISO Z39.86-2005).
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any
from src.config import METADATA


DTBOOK_NAMESPACE = "http://www.daisy.org/z3986/2005/dtbook/"
DOCTYPE_DECLARATION = '<!DOCTYPE dtbook PUBLIC "-//NISO//DTD dtbook 2005-3//EN" "http://www.daisy.org/z3986/2005/dtbook-2005-3.dtd">\n'


def build_dtbook_tree(chapter_data: Dict[str, Any], metadata: Dict[str, str] = METADATA) -> ET.Element:
    """
    Construct the ElementTree for DTBook 2005-3.
    """
    ET.register_namespace("", DTBOOK_NAMESPACE)

    dtbook = ET.Element(f"{{{DTBOOK_NAMESPACE}}}dtbook", {
        "xml:lang": metadata.get("dc:Language", "vi-VN"),
        "version": "2005-3"
    })

    # ===== HEAD =====
    head = ET.SubElement(dtbook, "head")

    # Required and extended meta tags
    meta_tags = [
        ("dtb:uid", metadata["dtb:uid"]),
        ("dtb:generator", metadata["dtb:generator"]),
        ("dc:Title", f"{metadata['dc:Title']} - {chapter_data['chapter_title']}"),
        ("dc:Creator", metadata["dc:Creator"]),
        ("dc:Date", metadata["dc:Date"]),
        ("dc:Publisher", metadata["dc:Publisher"]),
        ("dc:Identifier", metadata["dc:Identifier"]),
        ("dc:Language", metadata["dc:Language"]),
        ("dc:Subject", metadata["dc:Subject"]),
        ("dc:Description", metadata["dc:Description"]),
        ("note", metadata.get("note", "")),
    ]

    for name, content in meta_tags:
        if content:
            ET.SubElement(head, "meta", {"name": name, "content": content})

    # ===== BOOK =====
    book = ET.SubElement(dtbook, "book", {"showin": "blp"})

    # ===== FRONTMATTER =====
    frontmatter = ET.SubElement(book, "frontmatter")

    doctitle = ET.SubElement(frontmatter, "doctitle", {
        "id": "forsmil-1",
        "smilref": "mo0.smil#sforsmil-1"
    })
    ET.SubElement(doctitle, "sent", {
        "id": "id_1",
        "smilref": "mo0.smil#sid_1"
    }).text = metadata["dc:Title"]

    docauthor = ET.SubElement(frontmatter, "docauthor", {
        "id": "forsmil-2",
        "smilref": "mo0.smil#sforsmil-2"
    })
    ET.SubElement(docauthor, "sent", {
        "id": "id_2",
        "smilref": "mo0.smil#sid_2"
    }).text = metadata["dc:Creator"]

    # ===== BODYMATTER =====
    bodymatter = ET.SubElement(book, "bodymatter", {"id": "bodymatter_0001"})
    level1 = ET.SubElement(bodymatter, "level1")

    # Chapter heading (h1)
    h1 = ET.SubElement(level1, "h1", {
        "id": "faux-heading",
        "smilref": "mo0.smil#sfaux-heading"
    })
    ET.SubElement(h1, "sent", {
        "id": "id_3",
        "smilref": "mo0.smil#sid_3"
    }).text = chapter_data["chapter_title"]

    # Paragraphs and Sentences
    for para in chapter_data["paragraphs"]:
        p_elem = ET.SubElement(level1, "p", {
            "id": para["p_id"],
            "smilref": f"mo0.smil#{para['seq_id']}"
        })
        for sent in para["sentences"]:
            ET.SubElement(p_elem, "sent", {
                "id": sent["sent_id"],
                "smilref": f"mo0.smil#{sent['smil_sid']}"
            }).text = sent["text"]

    return dtbook


def generate_dtbook_xml_string(chapter_data: Dict[str, Any], metadata: Dict[str, str] = METADATA, pretty: bool = True) -> str:
    """
    Generate the complete DTBook XML string including XML declaration and DOCTYPE.
    """
    dtbook_elem = build_dtbook_tree(chapter_data, metadata)
    raw_xml_bytes = ET.tostring(dtbook_elem, encoding="utf-8")

    if pretty:
        # Use minidom to pretty print
        dom = minidom.parseString(raw_xml_bytes)
        # minidom toprettyxml generates its own <?xml ...?> so we extract the root
        ugly_xml = dom.documentElement.toxml(encoding="utf-8").decode("utf-8")
        # Format with clean indentation
        reparsed = minidom.parseString(ugly_xml)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        # Remove minidom's default XML declaration so we can prepend our standard one + DOCTYPE
        lines = pretty_xml.split("\n")
        if lines and lines[0].startswith("<?xml"):
            lines = lines[1:]
        body_xml = "\n".join(lines).strip()
    else:
        body_xml = raw_xml_bytes.decode("utf-8")

    final_xml = '<?xml version="1.0" encoding="utf-8"?>\n' + DOCTYPE_DECLARATION + body_xml + "\n"
    return final_xml


def save_dtbook_file(chapter_data: Dict[str, Any], output_path: str, metadata: Dict[str, str] = METADATA):
    """
    Save the DTBook XML to disk.
    """
    xml_content = generate_dtbook_xml_string(chapter_data, metadata)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
