import json, os, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.expanduser("~/.claude/skills/personal-brand-docs/scripts/build_docx.sh")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def build(src, comments_path, out, author="Claude", date="2026-11-05T00:00:00Z"):
    text = open(src).read().replace("`", "")
    comments = json.load(open(comments_path))
    missing = []
    for i, c in enumerate(comments):
        anchor = c["anchor"].replace("`", "")
        if anchor not in text:
            missing.append(anchor)
            continue
        wrapped = (f'[{c["comment"]}]{{.comment-start id="{i}" author="{author}" date="{date}"}}'
                   f'{anchor}[]{{.comment-end id="{i}"}}')
        text = text.replace(anchor, wrapped, 1)
    if missing:
        print("anchors not found:", file=sys.stderr)
        for m in missing:
            print("  " + m[:100], file=sys.stderr)
    tmp = os.path.join(os.environ.get("TMPDIR", tempfile.gettempdir()), os.path.basename(src))
    open(tmp, "w").write(text)
    subprocess.run(["bash", SKILL, tmp, out], check=True)
    with zipfile.ZipFile(out) as z:
        n = z.read("word/comments.xml").count(b"<w:comment ") if "word/comments.xml" in z.namelist() else 0
    print(f"{out}: {n} comments")


def read(docx):
    with zipfile.ZipFile(docx) as z:
        names = z.namelist()
        if "word/comments.xml" not in names:
            print("no comments in file")
            return
        comments = ET.fromstring(z.read("word/comments.xml"))
        doc = ET.fromstring(z.read("word/document.xml"))
    by_id = {}
    for c in comments.findall(f"{W}comment"):
        cid = c.get(f"{W}id")
        by_id[cid] = {"author": c.get(f"{W}author"), "text": "".join(t.text or "" for t in c.iter(f"{W}t")).strip()}
    anchored = {}
    active = {}
    for el in doc.iter():
        if el.tag == f"{W}commentRangeStart":
            active[el.get(f"{W}id")] = []
        elif el.tag == f"{W}commentRangeEnd":
            cid = el.get(f"{W}id")
            anchored[cid] = "".join(active.pop(cid, []))
        elif el.tag == f"{W}t":
            for buf in active.values():
                buf.append(el.text or "")
    for cid, c in by_id.items():
        print(f"[{cid}] {c['author']}: {c['text']}")
        print(f"    on: {anchored.get(cid, '')[:160]}")


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "read":
        read(sys.argv[2])
