"""Build a PDF report from a scan result. Stateless: nothing is stored on the server."""
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK = colors.HexColor("#111827")
BRAND = colors.HexColor("#0f766e")
LINE = colors.HexColor("#d1d5db")


def _t(value: Any, limit: int = 300) -> str:
    """Plain text, length-limited and escaped for ReportLab's mini-markup."""
    text = "" if value is None else str(value)
    return escape(text[:limit])


def _list(value: Any, limit: int = 150) -> List[str]:
    return [str(v) for v in value[:limit]] if isinstance(value, list) else []


def _pairs(value: Any, limit: int = 40) -> List[List[str]]:
    """[[label, value], ...] from a scan result; anything else is dropped."""
    if not isinstance(value, list):
        return []
    return [[str(p[0]), str(p[1])] for p in value[:limit]
            if isinstance(p, list) and len(p) >= 2 and isinstance(p[0], str) and isinstance(p[1], str) and p[1]]


def _styles():
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=INK, fontSize=20, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=BRAND, fontSize=13, spaceBefore=10, spaceAfter=6)
    body = ParagraphStyle("body", parent=styles["BodyText"], textColor=INK, fontSize=10, leading=14)
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.HexColor("#374151"), alignment=TA_CENTER)
    warn = ParagraphStyle("warn", parent=body, textColor=colors.HexColor("#b91c1c"), fontSize=11, spaceBefore=6, spaceAfter=6)
    return h1, h2, body, small, warn


def _fact_table(rows: List[List[str]], body) -> Table:
    table = Table([[Paragraph(f"<b>{_t(k, 60)}</b>", body), Paragraph(_t(v, 600), body)] for k, v in rows],
                  colWidths=[45 * mm, 120 * mm])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return table


def _finish(story: list, result: Dict[str, Any], site_name: str, sources: str) -> bytes:
    h1, h2, body, small, warn = _styles()
    code = result.get("code") if isinstance(result.get("code"), dict) else {}
    code_facts = _pairs(code.get("facts"))
    if code_facts:
        story += [Paragraph("Barcode details", h2), _fact_table(code_facts, body)]
    notes = _list(result.get("notes"), 10)
    if notes:
        story += [Spacer(1, 4 * mm)] + [Paragraph(_t(n, 400), body) for n in notes]
    story += [Spacer(1, 10 * mm), Paragraph(sources, small), Paragraph(_t(site_name, 80), small)]
    buf = BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                      leftMargin=20 * mm, rightMargin=20 * mm, title="Scan report").build(story)
    return buf.getvalue()


def _build_generic(result: Dict[str, Any], site_name: str) -> bytes:
    """Products, books and other codes (links, payments, Wi-Fi, text...)."""
    h1, h2, body, small, warn = _styles()
    item = result.get("item") if isinstance(result.get("item"), dict) else {}
    content = result.get("content") if isinstance(result.get("content"), dict) else {}
    title = item.get("title") or content.get("title") or result.get("title") or "Scanned code"
    story = [Paragraph(_t(title, 150), h1)]
    if item.get("subtitle"):
        story.append(Paragraph(_t(item["subtitle"], 150), body))
    story += [Paragraph("Report created " + datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"), body),
              Spacer(1, 4 * mm)]
    if isinstance(result.get("warning"), str) and result["warning"]:
        story.append(Paragraph("<b>Warning:</b> " + _t(result["warning"], 300), warn))
    facts = _pairs(item.get("facts") or content.get("facts"))
    if facts:
        story += [Paragraph("Details", h2), _fact_table(facts, body)]
    for heading, text in _pairs(item.get("sections"), 5):
        story += [Paragraph(_t(heading, 80), h2), Paragraph(_t(text, 3000), body)]
    if item.get("database"):
        story.append(Paragraph("Source: " + _t(item["database"], 60) + (f" ({_t(item.get('url'), 200)})" if item.get("url") else ""), body))
    return _finish(story, result, site_name,
                   "Product details from open databases (Open Food Facts family, Open Library); other details read "
                   "from the code itself. Check links and payment requests before you use them.")


def build_pdf(result: Dict[str, Any], site_name: str) -> bytes:
    if result.get("kind") in ("product", "book", "code"):
        return _build_generic(result, site_name)
    d = result.get("dashboard") if isinstance(result.get("dashboard"), dict) else {}
    off = result.get("open_food_facts") if isinstance(result.get("open_food_facts"), dict) else {}

    h1, h2, body, small, warn = _styles()

    story = [
        Paragraph(_t(d.get("Product Name"), 150), h1),
        Paragraph(_t(d.get("Brand"), 100), body),
        Paragraph("Report created " + datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"), body),
        Spacer(1, 6 * mm),
    ]
    if isinstance(result.get("warning"), str) and result["warning"]:
        story.append(Paragraph("<b>Warning:</b> " + _t(result["warning"], 300), warn))

    rows = [
        ["Barcode", _t(off.get("barcode") or "—", 20)],
        ["Vegetarian status", f"{_t(d.get('Veg Status'), 40)} — {_t(d.get('Veg Reason'), 120)}"],
        ["Nutri-Score", _t(off.get("nutriscore") or "Not enough data", 20)],
        ["NOVA group", _t(off.get("nova_group") or "—", 5)],
        ["Ingredient score", f"{_t(d.get('Safety Score'))}/100" if d.get("Safety Score") is not None else "Not available"],
    ]
    table = Table([[Paragraph(f"<b>{k}</b>", body), Paragraph(v, body)] for k, v in rows],
                  colWidths=[45 * mm, 120 * mm])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(table)

    ingredients = _list(d.get("Ingredients"))
    story += [Paragraph(f"Ingredients ({len(ingredients)})", h2),
              Paragraph(", ".join(_t(i, 200) for i in ingredients) or "No ingredients list available.", body)]

    allergens = _list(d.get("Allergens"), 30)
    story += [Paragraph("Possible allergens", h2),
              Paragraph(", ".join(_t(a, 60) for a in allergens) or "None detected in the ingredients text.", body)]

    flags = _list(d.get("Flags"), 30)
    story += [Paragraph("Ingredients to watch", h2),
              Paragraph(", ".join(_t(f, 80) for f in flags) or "Nothing flagged.", body)]

    nutr = off.get("nutriments") if isinstance(off.get("nutriments"), dict) else {}
    labels = [("energy-kcal_100g", "Energy", "kcal"), ("fat_100g", "Fat", "g"), ("saturated-fat_100g", "Saturated fat", "g"),
              ("carbohydrates_100g", "Carbohydrates", "g"), ("sugars_100g", "Sugars", "g"), ("fiber_100g", "Fibre", "g"),
              ("proteins_100g", "Protein", "g"), ("salt_100g", "Salt", "g")]
    nrows = [[name, f"{float(nutr[key]):.1f} {unit}"] for key, name, unit in labels
             if isinstance(nutr.get(key), (int, float))]
    if nrows:
        story.append(Paragraph("Nutrition per 100 g / 100 ml", h2))
        nt = Table(nrows, colWidths=[60 * mm, 40 * mm])
        nt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, LINE), ("FONTSIZE", (0, 0), (-1, -1), 10)]))
        story.append(nt)

    return _finish(story, result, site_name,
                   "Data from Open Food Facts (ODbL) and the product label. Allergen and vegetarian checks are "
                   "automatic and can miss things: always read the pack. Not medical advice.")
