from __future__ import annotations

import base64
import html
import json
import re
import urllib.parse
import zlib
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DRAWIO_PATH = DOCS / "dormflow-mindmap.drawio"
LINK_PATH = DOCS / "dormflow-mindmap-app-diagrams-link.txt"
MARKDOWN_PATH = DOCS / "mindmap.md"


def escape_label(value: str) -> str:
    escaped = html.escape(value, quote=True)
    return escaped.encode("ascii", "xmlcharrefreplace").decode("ascii")


def node(
    node_id: str,
    value: str,
    x: int,
    y: int,
    width: int,
    height: int,
    fill: str,
    stroke: str,
    font: str,
    *,
    font_size: int = 14,
    bold: bool = False,
    shape: str = "rounded=1;absoluteArcSize=1;arcSize=18;",
    stroke_width: int = 2,
) -> str:
    style = (
        f"{shape}whiteSpace=wrap;html=1;"
        f"fillColor={fill};strokeColor={stroke};strokeWidth={stroke_width};"
        f"fontColor={font};fontSize={font_size};spacing=12;"
        f"fontStyle={'1' if bold else '0'};"
    )
    return (
        f'<mxCell id="{node_id}" value="{escape_label(value)}" style="{style}" '
        f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" '
        f'width="{width}" height="{height}" as="geometry"/></mxCell>'
    )


def edge(
    edge_id: str,
    source: str,
    target: str,
    color: str,
    *,
    width: int = 4,
    exit_port: tuple[float, float] = (0.5, 0.5),
    entry_port: tuple[float, float] = (0.5, 0.5),
) -> str:
    exit_x, exit_y = exit_port
    entry_x, entry_y = entry_port
    style = (
        "edgeStyle=none;rounded=1;curved=1;html=1;"
        f"strokeColor={color};strokeWidth={width};endArrow=none;endFill=0;"
        f"exitX={exit_x};exitY={exit_y};exitDx=0;exitDy=0;"
        f"entryX={entry_x};entryY={entry_y};entryDx=0;entryDy=0;"
    )
    return (
        f'<mxCell id="{edge_id}" value="" style="{style}" edge="1" '
        f'parent="1" source="{source}" target="{target}">'
        '<mxGeometry relative="1" as="geometry"/></mxCell>'
    )


def title_node() -> str:
    return node(
        "title",
        "Интеллект-карта DormFlow",
        620,
        35,
        640,
        54,
        "#FFFFFF",
        "#FFFFFF",
        "#111827",
        font_size=26,
        bold=True,
        shape="rounded=0;",
        stroke_width=0,
    )


branches = [
    {
        "id": "goal",
        "title": "Цель",
        "pos": (790, 165, 230, 64),
        "color": "#E76F51",
        "leaf": "#FFF0EB",
        "font": "#3A160E",
        "center_exit": (0.52, 0.0),
        "branch_entry": (0.5, 1.0),
        "child_exit": (1.0, 0.5),
        "child_entry": (0.0, 0.5),
        "children": [
            ("goal_1", "Порядок в общежитии", 1125, 95, 250, 50),
            ("goal_2", "Меньше потерь в чатах", 1125, 165, 250, 50),
            ("goal_3", "Роли, статусы, история", 1125, 235, 250, 50),
        ],
    },
    {
        "id": "platforms",
        "title": "Платформы",
        "pos": (385, 165, 240, 64),
        "color": "#2A9D8F",
        "leaf": "#E7F7F4",
        "font": "#073A34",
        "center_exit": (0.1, 0.1),
        "branch_entry": (1.0, 0.5),
        "child_exit": (0.0, 0.5),
        "child_entry": (1.0, 0.5),
        "children": [
            ("platforms_1", "Android", 90, 70, 170, 48),
            ("platforms_2", "iOS", 90, 135, 170, 48),
            ("platforms_3", "Python / Kivy", 90, 200, 190, 48),
            ("platforms_4", "buildozer / kivy-ios", 90, 265, 230, 48),
        ],
    },
    {
        "id": "roles",
        "title": "Роли",
        "pos": (1255, 165, 220, 64),
        "color": "#8A5CF6",
        "leaf": "#F0EAFF",
        "font": "#2B145E",
        "center_exit": (0.9, 0.1),
        "branch_entry": (0.0, 0.5),
        "child_exit": (1.0, 0.5),
        "child_entry": (0.0, 0.5),
        "children": [
            ("roles_1", "Жилец", 1565, 80, 180, 48),
            ("roles_2", "Староста", 1565, 150, 190, 48),
            ("roles_3", "Администратор после MVP", 1565, 220, 250, 48),
        ],
    },
    {
        "id": "analogs",
        "title": "Аналоги",
        "pos": (370, 505, 240, 64),
        "color": "#607D8B",
        "leaf": "#EEF3F5",
        "font": "#172B33",
        "center_exit": (0.0, 0.48),
        "branch_entry": (1.0, 0.5),
        "child_exit": (0.0, 0.5),
        "child_entry": (1.0, 0.5),
        "children": [
            ("analogs_1", "Trello: доски вручную", 75, 395, 245, 48),
            ("analogs_2", "Telegram + Forms: чат", 75, 470, 245, 48),
            ("analogs_3", "Notion / Sheets: таблицы", 75, 545, 255, 48),
            ("analogs_4", "DormFlow: под общежитие", 75, 620, 255, 48),
        ],
    },
    {
        "id": "features",
        "title": "Функции MVP",
        "pos": (1255, 500, 250, 64),
        "color": "#F4A261",
        "leaf": "#FFF4E5",
        "font": "#4A2700",
        "center_exit": (1.0, 0.5),
        "branch_entry": (0.0, 0.5),
        "child_exit": (1.0, 0.5),
        "child_entry": (0.0, 0.5),
        "children": [
            ("features_1", "Регистрация и вход", 1570, 345, 220, 48),
            ("features_2", "Профиль комнаты", 1570, 410, 220, 48),
            ("features_3", "Дежурства", 1570, 475, 180, 48),
            ("features_4", "Заявки со статусами", 1570, 540, 250, 48),
            ("features_5", "Объявления", 1570, 605, 200, 48),
            ("features_6", "Голосования", 1570, 670, 200, 48),
        ],
    },
    {
        "id": "backend",
        "title": "Backend",
        "pos": (385, 840, 240, 64),
        "color": "#1E6091",
        "leaf": "#E8F4FF",
        "font": "#0B2D47",
        "center_exit": (0.1, 0.9),
        "branch_entry": (1.0, 0.5),
        "child_exit": (0.0, 0.5),
        "child_entry": (1.0, 0.5),
        "children": [
            ("backend_1", "FastAPI", 110, 735, 170, 48),
            ("backend_2", "SQLite", 110, 800, 170, 48),
            ("backend_3", "Токены доступа", 110, 865, 220, 48),
            ("backend_4", "Общие данные", 110, 930, 200, 48),
        ],
    },
    {
        "id": "scenarios",
        "title": "Сценарии",
        "pos": (800, 845, 230, 64),
        "color": "#264653",
        "leaf": "#E9F0F2",
        "font": "#10232B",
        "center_exit": (0.5, 1.0),
        "branch_entry": (0.5, 0.0),
        "child_exit": (0.5, 1.0),
        "child_entry": (0.5, 0.0),
        "children": [
            ("scenarios_1", "Отметить дежурство", 305, 1005, 230, 48),
            ("scenarios_2", "Создать заявку", 565, 1060, 200, 48),
            ("scenarios_3", "Новая -> в работе -> закрыта", 795, 1005, 290, 48),
            ("scenarios_4", "Опубликовать объявление", 1115, 1060, 270, 48),
            ("scenarios_5", "Проголосовать один раз", 1415, 1005, 240, 48),
        ],
    },
]


def build_xml() -> str:
    edge_cells: list[str] = []
    node_cells: list[str] = [
        title_node(),
        node(
            "center",
            "DormFlow",
            825,
            505,
            220,
            110,
            "#111827",
            "#111827",
            "#FFFFFF",
            font_size=24,
            bold=True,
            shape="ellipse;",
            stroke_width=3,
        ),
    ]

    edge_count = 1
    for branch in branches:
        branch_id = branch["id"]
        color = branch["color"]
        leaf_fill = branch["leaf"]
        font = branch["font"]
        x, y, w, h = branch["pos"]
        node_cells.append(
            node(branch_id, branch["title"], x, y, w, h, color, color, "#FFFFFF", font_size=17, bold=True)
        )
        edge_cells.append(
            edge(
                f"edge_{edge_count}",
                "center",
                branch_id,
                color,
                width=5,
                exit_port=branch["center_exit"],
                entry_port=branch["branch_entry"],
            )
        )
        edge_count += 1

        for child_id, title, cx, cy, cw, ch in branch["children"]:
            node_cells.append(node(child_id, title, cx, cy, cw, ch, leaf_fill, color, font, font_size=13))
            edge_cells.append(
                edge(
                    f"edge_{edge_count}",
                    branch_id,
                    child_id,
                    color,
                    width=3,
                    exit_port=branch["child_exit"],
                    entry_port=branch["child_entry"],
                )
            )
            edge_count += 1

    modified = datetime.now(timezone.utc).isoformat()
    body = "".join(['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>', *edge_cells, *node_cells])
    return (
        f'<mxfile host="app.diagrams.net" modified="{modified}" '
        'agent="Codex" version="24.7.17" type="device">'
        '<diagram id="dormflow-mindmap" name="DormFlow mind map">'
        '<mxGraphModel dx="1900" dy="1200" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="0" fold="1" page="1" pageScale="1" '
        'pageWidth="1900" pageHeight="1200" background="#FFFFFF" math="0" shadow="0">'
        f"<root>{body}</root>"
        "</mxGraphModel></diagram></mxfile>"
    )


def encode_uri_component(value: str) -> str:
    return urllib.parse.quote(value, safe="-_.!~*'()")


def compress_drawio_xml(xml: str) -> str:
    encoded_xml = encode_uri_component(xml).encode("utf-8")
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(encoded_xml) + compressor.flush()
    return base64.b64encode(compressed).decode("ascii")


def decompress_drawio_xml(data: str) -> str:
    encoded_xml = zlib.decompress(base64.b64decode(data), wbits=-15).decode("utf-8")
    return urllib.parse.unquote(encoded_xml)


def build_link(xml: str) -> str:
    payload = {
        "type": "xml",
        "compressed": True,
        "data": compress_drawio_xml(xml),
    }
    encoded_payload = urllib.parse.quote(json.dumps(payload, separators=(",", ":")), safe="")
    return f"https://app.diagrams.net/?pv=0&grid=0#create={encoded_payload}"


def validate(xml: str, link: str) -> None:
    ElementTree.fromstring(xml)
    if "?" in xml:
        raise RuntimeError("Unexpected question mark in drawio XML")
    if re.search(r"[\u0400-\u04FF]", xml):
        raise RuntimeError("Drawio XML must stay ASCII with numeric entities")
    fragment = link.split("#create=", 1)[1]
    payload = json.loads(urllib.parse.unquote(fragment))
    if payload["type"] != "xml" or payload.get("compressed") is not True:
        raise RuntimeError("Link must open the fixed drawio XML layout")
    restored = decompress_drawio_xml(payload["data"])
    if restored != xml:
        raise RuntimeError("Compressed link does not restore the drawio XML")
    if "DormFlow" not in restored or "mermaid" in link.lower():
        raise RuntimeError("Invalid app.diagrams.net link payload")


def build_markdown() -> str:
    return """# Интеллект-карта DormFlow

Основной файл для app.diagrams.net: [dormflow-mindmap.drawio](./dormflow-mindmap.drawio).

Ссылка для открытия карты в app.diagrams.net: [dormflow-mindmap-app-diagrams-link.txt](./dormflow-mindmap-app-diagrams-link.txt).

Карта сделана вручную в draw.io XML. Mermaid не используется, чтобы diagrams.net не ломал раскладку.

## Структура

- DormFlow
- Цель: порядок в общежитии, меньше потерь в чатах, роли/статусы/история
- Платформы: Android, iOS, Python/Kivy, buildozer/kivy-ios
- Роли: жилец, староста, администратор после MVP
- Backend: FastAPI, SQLite, токены доступа, общие данные
- Функции MVP: регистрация и вход, профиль комнаты, дежурства, заявки, объявления, голосования
- Аналоги: Trello, Telegram + Forms, Notion / Sheets, DormFlow
- Сценарии: дежурство, заявка, смена статуса, объявление, голосование
"""


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    xml = build_xml()
    link = build_link(xml)
    validate(xml, link)
    DRAWIO_PATH.write_text(xml, encoding="utf-8", newline="\n")
    LINK_PATH.write_text(link + "\n", encoding="utf-8", newline="\n")
    MARKDOWN_PATH.write_text(build_markdown(), encoding="utf-8", newline="\n")
    print(f"drawio_bytes={DRAWIO_PATH.stat().st_size}")
    print(f"link_chars={len(link)}")
    print(f"markdown_bytes={MARKDOWN_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
