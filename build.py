#!/usr/bin/env python3
"""从上游 m3u 构建 JSON 到 dist/。

特性:
  - 零第三方依赖（仅标准库）
  - 多源降级: raw.githubusercontent -> jsDelivr -> ghproxy -> gh-proxy
  - 原子写: 临时文件 + os.replace，绝不产生半截 JSON
  - 代理: 默认走系统代理，可用环境变量 M3U_PROXY 覆盖
"""
import json, os, re, sys, tempfile, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
sys.path.insert(0, ROOT)

from convert import parse  # noqa: E402

RAW_RE = re.compile(r"^https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$")
UA = "Mozilla/5.0 (compatible; m3u2json/1.0; +https://github.com)"


def _opener():
    env_proxy = os.environ.get("M3U_PROXY") or os.environ.get("HTTPS_PROXY")
    if env_proxy:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler({"http": env_proxy, "https": env_proxy})
        )
    return urllib.request.build_opener()


def candidates(url):
    """为 raw.githubusercontent 地址生成镜像降级链。"""
    out = [url]
    m = RAW_RE.match(url)
    if m:
        user, repo, branch, path = m.groups()
        out.append("https://cdn.jsdelivr.net/gh/%s/%s@%s/%s" % (user, repo, branch, path))
        out.append("https://ghproxy.net/" + url)
        out.append("https://gh-proxy.com/" + url)
    return out


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with _opener().open(req, timeout=timeout) as resp:
        return resp.read()


def atomic_write(path, text):
    """先写临时文件再原子替换，避免 web 端读到半截内容。"""
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


def build_one(job):
    target = os.path.join(DIST, job["file"])
    last_err = None
    for cand in candidates(job["source"]):
        try:
            raw = fetch(cand)
            items = parse(raw.decode("utf-8-sig", errors="replace"))
            if not items:
                raise ValueError("解析出 0 条记录")
            atomic_write(target, json.dumps(items, ensure_ascii=False, indent=2) + "\n")
            return len(items), cand
        except Exception as exc:  # noqa: BLE001
            last_err = "%s -> %s: %s" % (cand, type(exc).__name__, exc)
            print("    [降级] %s" % last_err, file=sys.stderr)
    raise RuntimeError("全部源都失败, 最后错误: %s" % last_err)


def main():
    cfg_path = os.path.join(ROOT, "sources.json")
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

    jobs = cfg.get("outputs", [])
    if not jobs:
        print("sources.json 里没有 outputs", file=sys.stderr)
        return 1

    failures = 0
    for job in jobs:
        print("[构建] %s  <-  %s" % (job["file"], job["source"]))
        try:
            count, used = build_one(job)
            size = os.path.getsize(os.path.join(DIST, job["file"]))
            print("  [OK] %d 条, %d 字节, 实际源: %s" % (count, size, used))
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print("  [FAIL] %s" % exc, file=sys.stderr)

    print()
    print("完成: %d 个成功, %d 个失败" % (len(jobs) - failures, failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
