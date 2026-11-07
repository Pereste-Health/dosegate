import re
import string
import sys

PUNCT = set(string.punctuation)


def esc(s):
    return "".join("\\" + c if c in PUNCT else c for c in s)


def prep(text):
    out = []
    for line in text.split("\n"):
        if line.lstrip().startswith("<!--") or re.match(r"^\s*\|?\s*:?-{3,}", line):
            out.append(line)
            continue
        parts = re.split(r"(`[^`\n]+`)", line)
        for i, p in enumerate(parts):
            if p.startswith("`") and p.endswith("`") and len(p) > 1:
                body = p[1:-1]
                parts[i] = esc(body)
                if body.startswith("--"):
                    word, _, rest = body.partition(" ")
                    parts[i] = f'[{esc(word)}]{{style="white-space:nowrap"}}' + (" " + esc(rest) if rest else "")
            else:
                parts[i] = re.sub(r"(?<![-\\])--(?=[A-Za-z])", r"\\-\\-", p)
        out.append("".join(parts))
    return "\n".join(out).replace("Forall₂", "Forall~2~")


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    open(dst, "w").write(prep(open(src).read()))
