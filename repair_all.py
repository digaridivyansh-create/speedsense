from pathlib import Path

root = Path("app")

bad_to_good = {
    "â‚¹": "₹",
    "âš¡": "⚡",
    "âœ¦": "✦",
    "â†»": "↻",
    "â—ˆ": "◆",
    "â€”": "—",
    "â€“": "–",
    "â€™": "’",
    "â€œ": "“",
    "â€": "”",
}

extensions = {".html", ".css", ".js", ".py"}

for p in root.rglob("*"):
    if not p.is_file():
        continue
    if p.suffix.lower() not in extensions:
        continue
    if ".before-" in p.name:
        continue

    try:
        raw = p.read_bytes()

        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
            text = raw.decode("utf-16")
        else:
            text = raw.decode("utf-8")

        original = text

        for bad, good in bad_to_good.items():
            text = text.replace(bad, good)

        if text != original:
            p.write_text(text, encoding="utf-8", newline="")
            print("FIXED:", p)
        else:
            print("OK:", p)

    except Exception as e:
        print("SKIPPED:", p, "-", e)
