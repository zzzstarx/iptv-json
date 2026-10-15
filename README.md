# iptv-json

把在线 m3u 转成 JSON，托管在 GitHub Pages / raw 上给客户端用。

## 目录结构

```
.
├─ convert.py          # 转换内核（零依赖，与 m3ujson.exe 输出全等）
├─ build.py            # 批量构建：多源降级 + 原子写
├─ sources.json        # 要转换哪些源（加一行 = 多一个产物）
├─ dist/               # 产物目录（构建后生成，浏览器可直接访问）
│   └─ Gather.json
└─ .github/workflows/
    └─ build.yml       # 每 6 小时自动刷新
```

## 本地构建

```bash
python build.py
```

跑完看 `dist/Gather.json`。

## 访问地址（二选一）

**raw 直链**（最简单，不用开 Pages）
```
https://raw.githubusercontent.com/<用户名>/<仓库名>/main/dist/Gather.json
```

**GitHub Pages**（Content-Type 正确，客户端更不容易挑食）
```
设置 → Pages → Source 选 "Deploy from a branch"
Branch 选 main，目录选 /(root) → Save
等 1~2 分钟
访问 https://<用户名>.github.io/<仓库名>/dist/Gather.json
```

## 降级链

构建时默认按下面的顺序试，前一个失败自动换下一个：

1. `raw.githubusercontent.com`（原始地址）
2. `cdn.jsdelivr.net`（jsDelivr，对 raw 的 CDN 加速）
3. `ghproxy.net`
4. `gh-proxy.com`

GitHub Actions 跑在海外，天然不受墙影响，所以自动刷新不会断。

## 走代理（本机在国内时需要）

```powershell
$env:M3U_PROXY = "http://127.0.0.1:7890"
python build.py
```

```bash
M3U_PROXY=http://127.0.0.1:7890 python build.py
```

## 加新源

编辑 `sources.json`：

```json
{
  "outputs": [
    {
      "file": "Gather.json",
      "source": "https://raw.githubusercontent.com/YanG-1989/m3u/main/Gather.m3u"
    },
    {
      "file": "Another.json",
      "source": "https://raw.githubusercontent.com/某人/某仓/main/某文件.m3u"
    }
  ]
}
```

多一行就多一个产物，互不影响。

## 客户端用

Tvbox / 影视仓等客户端里，把上面的 URL 填进"配置地址"即可。
