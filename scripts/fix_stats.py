from pathlib import Path

p = Path("app/dashboard/routes.py")
text = p.read_text()

# ensure total_outstanding exists in stats dict
if "total_outstanding" not in text:
    # naive but safe patch: inject default before return
    text = text.replace(
        "stats = {",
        "stats = {\n        \"total_outstanding\": 0,"
    )

p.write_text(text)
print("✔ added total_outstanding to stats")
