"""
Work out what a scanned code is, using only what the code itself contains.

- Product barcodes (EAN-13, EAN-8, UPC-A, UPC-E, GTIN-14), checked with the
  GS1 check digit, plus where the number was registered (GS1 prefix).
- ISBN (books) and ISSN (magazines).
- GS1 element strings (GS1-128 / GS1 DataMatrix on medicines and fresh food):
  product number, expiry, batch, serial.
- QR / other 2D content: links, UPI payments, Wi-Fi, contacts, email, phone,
  SMS, map locations, calendar events, plain text.

Nothing is looked up or guessed here; the network lookups live in lookup.py.
"""
import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

MAX_CODE_LENGTH = 4096  # the largest QR code holds about 4,300 characters

# GS1 member organisations by company prefix. The prefix shows which national
# GS1 office issued the number, not the country where the product was made.
# Source: GS1 company prefix list (gs1.org/standards/id-keys/company-prefix).
_GS1_PREFIXES: List[Tuple[int, int, str]] = [
    (0, 19, "GS1 US (USA and Canada)"), (20, 29, "Restricted circulation (store-internal number)"),
    (30, 39, "GS1 US (USA and Canada)"), (40, 49, "Restricted circulation (store-internal number)"),
    (50, 59, "GS1 US coupons"), (60, 139, "GS1 US (USA and Canada)"),
    (200, 299, "Restricted circulation (store-internal number)"),
    (300, 379, "GS1 France"), (380, 380, "GS1 Bulgaria"), (383, 383, "GS1 Slovenia"), (385, 385, "GS1 Croatia"),
    (387, 387, "GS1 Bosnia and Herzegovina"), (389, 389, "GS1 Montenegro"), (400, 440, "GS1 Germany"),
    (450, 459, "GS1 Japan"), (460, 469, "GS1 Russia"), (471, 471, "GS1 Taiwan"), (474, 474, "GS1 Estonia"),
    (475, 475, "GS1 Latvia"), (477, 477, "GS1 Lithuania"), (479, 479, "GS1 Sri Lanka"), (480, 480, "GS1 Philippines"),
    (481, 481, "GS1 Belarus"), (482, 482, "GS1 Ukraine"), (484, 484, "GS1 Moldova"), (485, 485, "GS1 Armenia"),
    (486, 486, "GS1 Georgia"), (487, 487, "GS1 Kazakhstan"), (489, 489, "GS1 Hong Kong"), (490, 499, "GS1 Japan"),
    (500, 509, "GS1 UK"), (520, 521, "GS1 Greece"), (528, 528, "GS1 Lebanon"), (529, 529, "GS1 Cyprus"),
    (530, 530, "GS1 Albania"), (531, 531, "GS1 North Macedonia"), (535, 535, "GS1 Malta"), (539, 539, "GS1 Ireland"),
    (540, 549, "GS1 Belgium and Luxembourg"), (560, 560, "GS1 Portugal"), (569, 569, "GS1 Iceland"),
    (570, 579, "GS1 Denmark"), (590, 590, "GS1 Poland"), (594, 594, "GS1 Romania"), (599, 599, "GS1 Hungary"),
    (600, 601, "GS1 South Africa"), (603, 603, "GS1 Ghana"), (604, 604, "GS1 Senegal"), (608, 608, "GS1 Bahrain"),
    (609, 609, "GS1 Mauritius"), (611, 611, "GS1 Morocco"), (613, 613, "GS1 Algeria"), (615, 615, "GS1 Nigeria"),
    (616, 616, "GS1 Kenya"), (618, 618, "GS1 Côte d'Ivoire"), (619, 619, "GS1 Tunisia"), (620, 620, "GS1 Tanzania"),
    (621, 621, "GS1 Syria"), (622, 622, "GS1 Egypt"), (624, 624, "GS1 Libya"), (625, 625, "GS1 Jordan"),
    (626, 626, "GS1 Iran"), (627, 627, "GS1 Kuwait"), (628, 628, "GS1 Saudi Arabia"), (629, 629, "GS1 UAE"),
    (640, 649, "GS1 Finland"), (680, 681, "GS1 China"), (690, 699, "GS1 China"), (700, 709, "GS1 Norway"),
    (729, 729, "GS1 Israel"), (730, 739, "GS1 Sweden"), (740, 740, "GS1 Guatemala"), (741, 741, "GS1 El Salvador"),
    (742, 742, "GS1 Honduras"), (743, 743, "GS1 Nicaragua"), (744, 744, "GS1 Costa Rica"), (745, 745, "GS1 Panama"),
    (746, 746, "GS1 Dominican Republic"), (750, 750, "GS1 Mexico"), (754, 755, "GS1 Canada"), (759, 759, "GS1 Venezuela"),
    (760, 769, "GS1 Switzerland"), (770, 771, "GS1 Colombia"), (773, 773, "GS1 Uruguay"), (775, 775, "GS1 Peru"),
    (777, 777, "GS1 Bolivia"), (778, 779, "GS1 Argentina"), (780, 780, "GS1 Chile"), (784, 784, "GS1 Paraguay"),
    (786, 786, "GS1 Ecuador"), (789, 790, "GS1 Brazil"), (800, 839, "GS1 Italy"), (840, 849, "GS1 Spain"),
    (850, 850, "GS1 Cuba"), (858, 858, "GS1 Slovakia"), (859, 859, "GS1 Czech Republic"), (860, 860, "GS1 Serbia"),
    (865, 865, "GS1 Mongolia"), (867, 867, "GS1 North Korea"), (868, 869, "GS1 Türkiye"), (870, 879, "GS1 Netherlands"),
    (880, 881, "GS1 South Korea"), (883, 883, "GS1 Myanmar"), (884, 884, "GS1 Cambodia"), (885, 885, "GS1 Thailand"),
    (888, 888, "GS1 Singapore"), (890, 890, "GS1 India"), (893, 893, "GS1 Vietnam"), (894, 894, "GS1 Bangladesh"),
    (896, 896, "GS1 Pakistan"), (899, 899, "GS1 Indonesia"), (900, 919, "GS1 Austria"), (930, 939, "GS1 Australia"),
    (940, 949, "GS1 New Zealand"), (950, 950, "GS1 Global Office"), (955, 955, "GS1 Malaysia"), (958, 958, "GS1 Macau"),
    (977, 977, "Magazine or newspaper (ISSN)"), (978, 979, "Book (ISBN)"), (980, 980, "Refund receipt"),
    (981, 984, "Coupon"), (990, 999, "Coupon"),
]

_FORMAT_NAMES = {
    "QRCODE": "QR code", "MICROQRCODE": "Micro QR code", "MICROQR": "Micro QR code", "RMQRCODE": "rMQR code",
    "EAN13": "EAN-13", "EAN8": "EAN-8", "UPCA": "UPC-A", "UPCE": "UPC-E", "CODE128": "Code 128", "CODE39": "Code 39",
    "CODE93": "Code 93", "CODABAR": "Codabar", "ITF": "ITF", "ITF14": "ITF-14", "DATAMATRIX": "Data Matrix",
    "PDF417": "PDF417", "AZTEC": "Aztec", "MAXICODE": "MaxiCode", "RSS14": "GS1 DataBar", "DATABAR": "GS1 DataBar",
    "RSSEXPANDED": "GS1 DataBar Expanded", "DATABAREXPANDED": "GS1 DataBar Expanded",
    "DATABARLIMITED": "GS1 DataBar Limited", "TYPED": "Typed in",
}


def format_name(raw: Optional[str]) -> Optional[str]:
    """'QR_CODE', 'qrCode', 'BarcodeFormat.QRCode' -> 'QR code'. Unknown -> None."""
    if not isinstance(raw, str):
        return None
    key = re.sub(r"[^A-Z0-9]", "", raw.split(".")[-1].upper())
    return _FORMAT_NAMES.get(key)


# --------------------------------------------------------------------------
# Product numbers (GTIN), ISBN, ISSN
# --------------------------------------------------------------------------
def gtin_check_ok(digits: str) -> bool:
    if not digits.isdigit() or len(digits) not in (8, 12, 13, 14):
        return False
    body, check = digits[:-1], int(digits[-1])
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return (10 - total % 10) % 10 == check


def upce_to_upca(code: str) -> Optional[str]:
    """Expand an 8-digit UPC-E to its 12-digit UPC-A form."""
    if not re.fullmatch(r"[01]\d{7}", code):
        return None
    n, d, c = code[0], code[1:7], code[7]
    last = d[5]
    if last in "012":
        middle = d[0:2] + last + "0000" + d[2:5]
    elif last == "3":
        middle = d[0:3] + "00000" + d[3:5]
    elif last == "4":
        middle = d[0:4] + "00000" + d[4]
    else:
        middle = d[0:5] + "0000" + last
    return n + middle + c


def isbn10_to_13(isbn10: str) -> Optional[str]:
    s = isbn10.upper()
    if not re.fullmatch(r"\d{9}[\dX]", s):
        return None
    total = sum((10 - i) * (10 if ch == "X" else int(ch)) for i, ch in enumerate(s))
    if total % 11:
        return None
    body = "978" + s[:9]
    check = (10 - sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(body)) % 10) % 10
    return body + str(check)


def gs1_prefix(gtin13: str) -> Optional[str]:
    """Who issued this number, from the first three digits (of the 13-digit form)."""
    p = int(gtin13[:3])
    for lo, hi, name in _GS1_PREFIXES:
        if lo <= p <= hi:
            return name
    return None


def _issn_from_ean(ean: str) -> str:
    body = ean[3:10]
    total = sum(int(d) * (8 - i) for i, d in enumerate(body))
    check = (11 - total % 11) % 11
    return f"{body[:4]}-{body[4:]}{'X' if check == 10 else check}"


def describe_gtin(digits: str, fmt: Optional[str] = None) -> Optional[Dict]:
    """Facts about a product number, or None if the digits aren't a valid GTIN."""
    if fmt == "UPC-E" and len(digits) == 8:
        expanded = upce_to_upca(digits)
        if not expanded or not gtin_check_ok(expanded):
            return None
        digits, kind = expanded, "UPC-E (short UPC)"
    elif not gtin_check_ok(digits):
        return None
    else:
        if len(digits) == 14 and digits[0] == "0":
            digits = digits[1:]  # GS1 codes pad EAN-13 (and UPC-A) to 14 digits with a leading 0
        kind = {8: "EAN-8", 12: "UPC-A", 13: "EAN-13", 14: "GTIN-14 (outer case or pack)"}[len(digits)]

    if len(digits) == 8:
        lookup = digits
        # EAN-8 numbers starting 0 or 2 are for in-store use; the rest use the
        # same three-digit GS1 prefixes as EAN-13 (1xx isn't allocated this way).
        if digits[0] in "02":
            issuer = "Restricted circulation (store-internal number)"
        elif digits[0] == "1" or digits.startswith("96"):
            issuer = None
        else:
            issuer = gs1_prefix(digits[:3])
    else:
        gtin13 = digits[-13:] if len(digits) == 14 else digits.zfill(13)
        lookup = gtin13
        issuer = gs1_prefix(gtin13)

    info = {"gtin": digits, "lookup": lookup, "kind": kind, "issuer": issuer,
            "is_isbn": lookup.startswith(("978", "979")) and len(lookup) == 13 and not lookup.startswith("9790"),
            "is_issn": lookup.startswith("977") and len(lookup) == 13,
            "is_restricted": bool(issuer and issuer.startswith("Restricted")),
            "is_coupon": bool(issuer and ("oupon" in issuer or "Refund" in issuer))}
    facts = [["Barcode type", kind], ["Number", digits], ["Check digit", "Valid"]]
    if info["is_isbn"]:
        facts.append(["ISBN", lookup])
    elif info["is_issn"]:
        facts.append(["ISSN", _issn_from_ean(lookup)])
    elif issuer:
        label = "Number type" if info["is_restricted"] or info["is_coupon"] else "Registered with"
        facts.append([label, issuer])
    info["facts"] = facts
    return info


# --------------------------------------------------------------------------
# GS1 element strings: (01) product, (17) expiry, (10) batch, (21) serial
# --------------------------------------------------------------------------
_GS = "\x1d"
_AI_FIXED = {"00": 18, "01": 14, "02": 14, "11": 6, "12": 6, "13": 6, "15": 6, "16": 6, "17": 6}
_AI_VAR = {"10": "Batch / lot", "21": "Serial number", "240": "Additional product ID", "400": "Order number"}
_AI_DATES = {"11": "Production date", "13": "Packaging date", "15": "Best before", "16": "Sell by", "17": "Expiry date"}


def _gs1_date(yymmdd: str) -> Optional[date]:
    try:
        yy, mm, dd = int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:])
        year = 2000 + yy if yy < 50 else 1900 + yy
        if dd == 0:  # "00" day means the last day of the month
            nxt = date(year + (mm == 12), mm % 12 + 1, 1)
            return date.fromordinal(nxt.toordinal() - 1)
        return date(year, mm, dd)
    except ValueError:
        return None


def parse_gs1(text: str) -> Optional[Dict[str, str]]:
    """Parse '(01)…(17)…(10)…' or raw '01…17…10…<GS>21…'. None if it isn't GS1."""
    s = text.strip()
    for sym in ("]C1", "]d2", "]Q3", "]e0"):
        if s.startswith(sym):
            s = s[len(sym):]
    fields: Dict[str, str] = {}
    if s.startswith("("):
        for ai, value in re.findall(r"\((\d{2,4})\)([^(]*)", s):
            fields[ai] = value.strip()
    else:
        if not re.match(r"^(01|02|00)\d", s):
            return None
        i = 0
        while i < len(s):
            if s[i] == _GS:
                i += 1
                continue
            ai = next((a for a in ("240", "400") if s.startswith(a, i)), s[i:i + 2])
            i += len(ai)
            if ai in _AI_FIXED:
                fields[ai] = s[i:i + _AI_FIXED[ai]]
                i += _AI_FIXED[ai]
            elif ai in _AI_VAR:
                end = s.find(_GS, i)
                end = len(s) if end < 0 else end
                fields[ai] = s[i:end]
                i = end
            else:
                return fields if "01" in fields else None
    if "01" not in fields or not re.fullmatch(r"\d{14}", fields["01"]):
        return None
    return fields


def describe_gs1(fields: Dict[str, str], today: Optional[date] = None) -> Tuple[List[List[str]], Optional[str]]:
    today = today or date.today()
    facts: List[List[str]] = []
    warning = None
    for ai, label in _AI_DATES.items():
        if ai in fields:
            d = _gs1_date(fields[ai])
            if not d:
                continue
            facts.append([label, d.strftime("%d %b %Y")])
            if ai == "17" and d < today:
                warning = f"Expired on {d.strftime('%d %b %Y')}. Do not use."
            elif ai == "15" and d < today and not warning:
                warning = f"Best-before date passed on {d.strftime('%d %b %Y')}."
    for ai, label in _AI_VAR.items():
        if fields.get(ai):
            facts.append([label, fields[ai]])
    return facts, warning


# --------------------------------------------------------------------------
# Other content (mostly QR codes)
# --------------------------------------------------------------------------
def _split_escaped(s: str, sep: str = ";") -> List[str]:
    parts, cur, esc = [], "", False
    for ch in s:
        if esc:
            cur += ch
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == sep:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)
    return parts


def _kv(body: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for part in _split_escaped(body):
        if ":" in part:
            k, v = part.split(":", 1)
            out.setdefault(k.strip().upper(), v)
    return out


def _vcard(text: str) -> List[List[str]]:
    facts = []
    labels = {"FN": "Name", "ORG": "Organisation", "TITLE": "Job title", "TEL": "Phone", "EMAIL": "Email",
              "URL": "Website", "ADR": "Address", "NOTE": "Note"}
    for line in re.split(r"\r?\n", text):
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.split(";")[0].upper()
        if key in labels and value.strip():
            if key == "ADR":
                value = ", ".join(p for p in value.split(";") if p.strip())
            facts.append([labels[key], value.strip()])
    if not any(f[0] == "Name" for f in facts):
        n = re.search(r"^N[;:](?:[^:]*:)?(.*)$", text, re.M)
        if n:
            facts.insert(0, ["Name", " ".join(p for p in reversed(n.group(1).split(";")[:2]) if p).strip()])
    return facts


def _ical_date(v: str) -> str:
    m = re.match(r"(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2}))?", v)
    if not m:
        return v
    y, mo, d, h, mi = m.groups()
    out = date(int(y), int(mo), int(d)).strftime("%d %b %Y")
    return f"{out} {h}:{mi}" + (" UTC" if v.endswith("Z") else "") if h else out


def describe_content(text: str) -> Dict:
    """Classify non-product text. Returns {type, title, facts, link?, warning?}."""
    s = text.strip()
    low = s.lower()

    if low.startswith(("http://", "https://")):
        u = urlparse(s)
        out = {"type": "link", "title": "Web link", "facts": [["Address", s], ["Website", u.hostname or ""]]}
        if u.scheme == "https" and u.hostname:
            out["link"] = s
            out["warning"] = "Check the website name before you open it. QR codes are sometimes used for scams."
        else:
            out["warning"] = "This link is not secure (no https). Avoid entering any details on it."
            if u.hostname:
                out["link"] = s
        return out

    if low.startswith("upi://"):
        q = {k.lower(): v[0] for k, v in parse_qs(urlparse(s).query).items()}
        facts = [["Pay to (UPI ID)", q.get("pa", "")]]
        if q.get("pn"):
            facts.append(["Payee name", q["pn"]])
        if q.get("am"):
            facts.append(["Amount", f"{q['am']} {q.get('cu', 'INR')}"])
        if q.get("tn"):
            facts.append(["Note", q["tn"]])
        return {"type": "upi", "title": "UPI payment request", "facts": [f for f in facts if f[1]],
                "warning": "Scanning a QR code never gives you money. Only pay if you meant to pay this person."}

    if s.upper().startswith("WIFI:"):
        kv = _kv(s[5:])
        security = {"WPA": "WPA/WPA2", "WEP": "WEP", "NOPASS": "None (open network)", "": "None (open network)"}
        facts = [["Network name", kv.get("S", "")], ["Security", security.get(kv.get("T", "").upper(), kv.get("T", ""))]]
        if kv.get("P"):
            facts.append(["Password", kv["P"]])
        if kv.get("H", "").lower() == "true":
            facts.append(["Hidden network", "Yes"])
        return {"type": "wifi", "title": "Wi-Fi network", "facts": [f for f in facts if f[1]]}

    if s.upper().startswith("BEGIN:VCARD"):
        return {"type": "contact", "title": "Contact card", "facts": _vcard(s)}

    if s.upper().startswith("MECARD:"):
        kv = _kv(s[7:])
        name = kv.get("N", "").replace(",", " ").strip()
        facts = [["Name", name], ["Phone", kv.get("TEL", "")], ["Email", kv.get("EMAIL", "")],
                 ["Address", kv.get("ADR", "")], ["Website", kv.get("URL", "")], ["Note", kv.get("NOTE", "")]]
        return {"type": "contact", "title": "Contact card", "facts": [f for f in facts if f[1]]}

    if "BEGIN:VEVENT" in s.upper():
        facts = []
        for key, label in (("SUMMARY", "Event"), ("DTSTART", "Starts"), ("DTEND", "Ends"), ("LOCATION", "Place"), ("DESCRIPTION", "Details")):
            m = re.search(rf"^{key}[^:\n]*:(.*)$", s, re.M | re.I)
            if m and m.group(1).strip():
                v = m.group(1).strip()
                facts.append([label, _ical_date(v) if key.startswith("DT") else v])
        return {"type": "event", "title": "Calendar event", "facts": facts}

    if low.startswith("mailto:"):
        u = urlparse(s)
        q = {k.lower(): v[0] for k, v in parse_qs(u.query).items()}
        facts = [["To", unquote(u.path)], ["Subject", q.get("subject", "")], ["Message", q.get("body", "")]]
        return {"type": "email", "title": "Email", "facts": [f for f in facts if f[1]]}

    if s.upper().startswith("MATMSG:"):
        kv = _kv(s[7:])
        facts = [["To", kv.get("TO", "")], ["Subject", kv.get("SUB", "")], ["Message", kv.get("BODY", "")]]
        return {"type": "email", "title": "Email", "facts": [f for f in facts if f[1]]}

    if low.startswith("tel:"):
        return {"type": "phone", "title": "Phone number", "facts": [["Number", unquote(s[4:])]]}

    if low.startswith(("smsto:", "sms:")):
        rest = s.split(":", 1)[1]
        number, _, message = rest.partition(":")
        if "?" in number:
            number, _, query = number.partition("?")
            message = message or parse_qs(query).get("body", [""])[0]
        facts = [["Number", unquote(number)], ["Message", message]]
        return {"type": "sms", "title": "Text message", "facts": [f for f in facts if f[1]]}

    if low.startswith("geo:"):
        m = re.match(r"geo:(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)", low)
        if m and abs(float(m.group(1))) <= 90 and abs(float(m.group(2))) <= 180:
            lat, lng = m.group(1), m.group(2)
            return {"type": "location", "title": "Map location", "facts": [["Latitude", lat], ["Longitude", lng]],
                    "link": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lng}#map=16/{lat}/{lng}"}

    if re.fullmatch(r"\d+", s):
        return {"type": "number", "title": "Number", "facts": [["Number", s], ["Digits", str(len(s))]],
                "note": "This number is not a product barcode, so there is nothing to look up. "
                        "It may be a serial number, ticket or internal code."}

    return {"type": "text", "title": "Text", "facts": [["Text", s], ["Characters", str(len(s))]]}


def gs1_digital_link_gtin(text: str) -> Optional[str]:
    """GS1 Digital Link QR codes put the product number in the URL: …/01/<GTIN>."""
    m = re.match(r"^https?://[^/]+(?:/[^/]+)*?/01/(\d{8,14})(?:[/?#]|$)", text.strip(), re.I)
    return m.group(1) if m else None
