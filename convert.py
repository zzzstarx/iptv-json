#!/usr/bin/env python3
"""m3u -> json 转换内核（与 m3ujson.exe 输出逐字段等价，零第三方依赖）"""
import json, re, sys, urllib.request


def parse(text):
    """解析 m3u 文本，返回 [{"id", "name", "source"}, ...]"""
    items, cur = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            name = line.rsplit(",", 1)[-1].strip() if "," in line else ""
            cur = {"name": name}
        elif line.startswith("#"):
            continue
        else:
            if cur is not None:
                items.append({"id": len(items) + 1, "name": cur["name"], "source": line})
            cur = None
    return items


def main():
    if len(sys.argv) < 2:
        print("usage: convert.py <file-or-url>", file=sys.stderr)
        return 2
    src = sys.argv[1]
    if re.match(r"^https?://", src):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=30).read()
    else:
        raw = open(src, "rb").read()
    text = raw.decode("utf-8-sig", errors="replace")
    out = sys.stdout
    try:
        out.reconfigure(encoding="utf-8")
    except Exception:
        pass
    json.dump(parse(text), out, ensure_ascii=False, indent=2)
    out.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
