#!/usr/bin/env python3
"""Structural audit for editable diagrams.net/draw.io flowcharts.

The script accepts compressed or uncompressed .drawio files. It reports XML,
cell-reference, geometry, connector, and decision-label issues. With
--compare-original it also verifies that every original page and cell remains
unchanged in a preserve-and-append workflow.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class Finding:
    severity: str
    page: str
    cell: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "page": self.page,
            "cell": self.cell,
            "message": self.message,
        }


@dataclass
class Audit:
    path: str
    pages: int = 0
    vertices: int = 0
    edges: int = 0
    findings: list[Finding] = field(default_factory=list)

    def add(self, severity: str, page: str, cell: str, message: str) -> None:
        self.findings.append(Finding(severity, page, cell, message))

    @property
    def errors(self) -> int:
        return sum(item.severity == "ERROR" for item in self.findings)

    @property
    def warnings(self) -> int:
        return sum(item.severity == "WARNING" for item in self.findings)


def decode_diagram(diagram: ET.Element) -> ET.Element:
    model = diagram.find("mxGraphModel")
    if model is not None:
        return model

    payload = (diagram.text or "").strip()
    if not payload:
        raise ValueError("diagram has neither mxGraphModel XML nor compressed content")

    try:
        compressed = base64.b64decode(payload)
        xml_text = zlib.decompress(compressed, -15).decode("utf-8")
        xml_text = urllib.parse.unquote(xml_text)
        model = ET.fromstring(xml_text)
    except Exception as exc:  # noqa: BLE001 - report decoder context to user
        raise ValueError(f"cannot decode compressed diagram: {exc}") from exc

    if model.tag != "mxGraphModel":
        raise ValueError(f"decoded root is {model.tag!r}, expected 'mxGraphModel'")
    return model


def load_models(path: Path) -> list[tuple[str, str, ET.Element]]:
    root = ET.parse(path).getroot()
    if root.tag == "mxGraphModel":
        return [("page-1", "Page-1", root)]
    if root.tag != "mxfile":
        raise ValueError(f"root element is {root.tag!r}, expected 'mxfile'")

    models: list[tuple[str, str, ET.Element]] = []
    for index, diagram in enumerate(root.findall("diagram"), start=1):
        page_id = diagram.get("id") or f"page-{index}"
        page_name = diagram.get("name") or f"Page-{index}"
        models.append((page_id, page_name, decode_diagram(diagram)))
    if not models:
        raise ValueError("mxfile contains no diagram pages")
    return models


def style_map(style: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in style.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            result[key] = value
        elif item:
            result[item] = "1"
    return result


def geometry(cell: ET.Element) -> ET.Element | None:
    return cell.find("mxGeometry")


def point(geo: ET.Element | None, tag: str) -> tuple[float, float] | None:
    if geo is None:
        return None
    node = geo.find(f"mxPoint[@as='{tag}']")
    if node is None or node.get("x") is None or node.get("y") is None:
        return None
    try:
        return float(node.get("x", "0")), float(node.get("y", "0"))
    except ValueError:
        return None


def is_decision(cell: ET.Element) -> bool:
    style = style_map(cell.get("style", ""))
    return "rhombus" in style or style.get("shape") == "rhombus"


def is_blank(value: str | None) -> bool:
    if value is None:
        return True
    text = value.replace("&nbsp;", " ").replace("<br>", " ").strip()
    return not text


def cell_signature(cell: ET.Element) -> dict[str, object]:
    geo = geometry(cell)
    children = []
    if geo is not None:
        for child in geo:
            children.append(
                {
                    "tag": child.tag,
                    "attrs": sorted(child.attrib.items()),
                    "text": child.text or "",
                }
            )
    return {
        "attrs": sorted(cell.attrib.items()),
        "geometry_attrs": sorted(geo.attrib.items()) if geo is not None else None,
        "geometry_children": children,
    }


def signatures(path: Path) -> dict[str, dict[str, dict[str, object]]]:
    result: dict[str, dict[str, dict[str, object]]] = {}
    for page_id, _page_name, model in load_models(path):
        root = model.find("root")
        if root is None:
            result[page_id] = {}
            continue
        result[page_id] = {
            cell.get("id", ""): cell_signature(cell)
            for cell in root.findall("mxCell")
            if cell.get("id") is not None
        }
    return result


def audit_page(audit: Audit, page_name: str, model: ET.Element) -> None:
    root = model.find("root")
    if root is None:
        audit.add("ERROR", page_name, "", "mxGraphModel has no root element")
        return

    cells = root.findall("mxCell")
    ids: dict[str, ET.Element] = {}
    duplicates: set[str] = set()
    for cell in cells:
        cell_id = cell.get("id", "")
        if not cell_id:
            audit.add("ERROR", page_name, "", "mxCell is missing an id")
        elif cell_id in ids:
            duplicates.add(cell_id)
        else:
            ids[cell_id] = cell
    for cell_id in sorted(duplicates):
        audit.add("ERROR", page_name, cell_id, "duplicate cell id")

    vertices = [cell for cell in cells if cell.get("vertex") == "1"]
    edges = [cell for cell in cells if cell.get("edge") == "1"]
    audit.vertices += len(vertices)
    audit.edges += len(edges)

    for cell in cells:
        cell_id = cell.get("id", "")
        parent = cell.get("parent")
        if parent and parent not in ids:
            audit.add("ERROR", page_name, cell_id, f"missing parent cell {parent!r}")

    for cell in vertices:
        cell_id = cell.get("id", "")
        geo = geometry(cell)
        if geo is None:
            audit.add("ERROR", page_name, cell_id, "vertex has no mxGeometry")
            continue
        try:
            width = float(geo.get("width", "0"))
            height = float(geo.get("height", "0"))
        except ValueError:
            audit.add("ERROR", page_name, cell_id, "vertex geometry is not numeric")
            continue
        if width <= 0 or height <= 0:
            audit.add("ERROR", page_name, cell_id, "vertex width and height must be positive")

    outgoing: dict[str, list[ET.Element]] = {}
    for cell in edges:
        cell_id = cell.get("id", "")
        source = cell.get("source")
        target = cell.get("target")
        if source:
            outgoing.setdefault(source, []).append(cell)
            if source not in ids:
                audit.add("ERROR", page_name, cell_id, f"missing source cell {source!r}")
        if target and target not in ids:
            audit.add("ERROR", page_name, cell_id, f"missing target cell {target!r}")

        geo = geometry(cell)
        if geo is None:
            audit.add("ERROR", page_name, cell_id, "edge has no mxGeometry")
            continue
        start = point(geo, "sourcePoint")
        end = point(geo, "targetPoint")
        if not source and start is None:
            audit.add("WARNING", page_name, cell_id, "edge has no source cell or sourcePoint")
        if not target and end is None:
            audit.add("WARNING", page_name, cell_id, "edge has no target cell or targetPoint")
        if start is not None and end is not None and math.dist(start, end) < 0.01:
            audit.add("ERROR", page_name, cell_id, "edge sourcePoint equals targetPoint")

        style = style_map(cell.get("style", ""))
        if style.get("endArrow") == "none":
            audit.add("WARNING", page_name, cell_id, "control-flow edge has endArrow=none")

    for cell in vertices:
        if not is_decision(cell):
            continue
        cell_id = cell.get("id", "")
        branches = outgoing.get(cell_id, [])
        if len(branches) < 2:
            audit.add("WARNING", page_name, cell_id, "decision has fewer than two connected outgoing edges")
        for edge in branches:
            if is_blank(edge.get("value")):
                audit.add(
                    "WARNING",
                    page_name,
                    edge.get("id", ""),
                    f"outgoing edge from decision {cell_id!r} has no inline branch label",
                )


def compare_original(audit: Audit, original: Path, candidate: Path) -> None:
    try:
        before = signatures(original)
        after = signatures(candidate)
    except (ET.ParseError, OSError, ValueError) as exc:
        audit.add("ERROR", "preservation", "", f"cannot compare original: {exc}")
        return

    for page_id, original_cells in before.items():
        if page_id not in after:
            audit.add("ERROR", "preservation", page_id, "original page is missing")
            continue
        candidate_cells = after[page_id]
        for cell_id, signature in original_cells.items():
            if cell_id not in candidate_cells:
                audit.add("ERROR", "preservation", cell_id, "original cell is missing")
            elif candidate_cells[cell_id] != signature:
                audit.add("ERROR", "preservation", cell_id, "original cell was modified")


def run(path: Path, original: Path | None = None) -> Audit:
    audit = Audit(str(path))
    try:
        models = load_models(path)
    except (ET.ParseError, OSError, ValueError) as exc:
        audit.add("ERROR", "file", "", str(exc))
        return audit

    audit.pages = len(models)
    for _page_id, page_name, model in models:
        audit_page(audit, page_name, model)
    if original is not None:
        compare_original(audit, original, path)
    return audit


def print_text(audit: Audit) -> None:
    print(f"File: {audit.path}")
    print(f"Pages: {audit.pages}  Vertices: {audit.vertices}  Edges: {audit.edges}")
    print(f"Errors: {audit.errors}  Warnings: {audit.warnings}")
    for item in audit.findings:
        location = item.page
        if item.cell:
            location += f" / {item.cell}"
        print(f"{item.severity}: {location}: {item.message}")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("drawio_file", type=Path, help="candidate .drawio file")
    parser.add_argument(
        "--compare-original",
        type=Path,
        help="verify that all pages and cells in this original file remain unchanged",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser.parse_args(list(argv))


def main(argv: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(sys.argv[1:] if argv is None else argv)
    audit = run(args.drawio_file, args.compare_original)
    if args.json:
        print(
            json.dumps(
                {
                    "file": audit.path,
                    "pages": audit.pages,
                    "vertices": audit.vertices,
                    "edges": audit.edges,
                    "errors": audit.errors,
                    "warnings": audit.warnings,
                    "findings": [item.as_dict() for item in audit.findings],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print_text(audit)
    return 1 if audit.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
