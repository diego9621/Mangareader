import re

def clean_desc(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</p\s*>", "\n\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&mdash;", "—").replace("&quot;", "\"").replace("&amp;", "&")
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s

def fmt_date(d: dict) -> str:
    if not d:
        return ""
    y = d.get("year")
    m = d.get("month")
    day = d.get("day")
    if not y:
        return ""
    if m and day:
        return f"{y:04d}-{m:02d}-{day:02d}"
    if m:
        return f"{y:04d}-{m:02d}"
    return f"{y:04d}"