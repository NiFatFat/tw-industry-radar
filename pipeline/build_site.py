# -*- coding: utf-8 -*-
"""組雲端網站的靜態頁面：docs/index.html、docs/industry/{id}.html、docs/stock/{symbol}.html

讀三份資料：
  docs/data/radar.json   ← fetch_radar.py 產的（產業熱度＋產業裡有哪些股票）
  docs/data/prices/*.json ← fetch_prices.py 產的（K線＋均線）
  docs/data/flags.json   ← 本機 local_push_flags.py 推上來的（三套策略目前前15名）
                            這支腳本不寫這個檔，沒有就當作「還沒更新」，flame 全部是 0
  docs/data/names.json   ← fetch_prices.py 順便抓的股票中文名稱
"""
from __future__ import annotations
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = DOCS / "data"

STRAT_LABEL = {
    "fx": "外資買超策略（40日買超÷股本前15檔，已驗證）",
    "cb": "combo策略（營收年增×創新高前15檔，已驗證）",
    "sd": "自營自行策略（40日買超÷股本前15檔，⚠️觀察中、還沒驗證穩定）",
}

DISCLAIMER = """
<b>熱度資料</b>：來自 duang0615/tw-market-radar，是「過去72小時」的即時快照，不是歷史趨勢，不能拿來回測，也不代表「熱門產業之後會漲比較多」——這件事沒有驗證過。<br>
<b>🔥 火焰標記</b>：代表這檔股票「現在」符合哪些自家已驗證/觀察中的選股條件，不是投資建議、不是報酬保證、更不是目標價。自營自行策略目前只是觀察紀錄（IC t值僅1.49，還沒驗證穩定），不是已驗證策略。<br>
本頁僅供 AI 工具應用教學，不提供任何投資建議、不推薦任何個股、不保證任何投資績效。投資有風險，請謹慎評估並自負盈虧。
"""


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def esc(s):
    return html.escape(str(s)) if s is not None else ""


def page(title: str, body: str, depth: int = 0) -> str:
    base = "../" * depth
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{base}assets/style.css">
</head>
<body>
<header class="top">
  <h1><a href="{base}index.html">台股產業熱度雷達</a></h1>
  <span class="sub">產業熱度：duang0615/tw-market-radar　個股K線：FinMind</span>
</header>
<div class="wrap">
{body}
<footer class="disclaimer">{DISCLAIMER}</footer>
</div>
</body>
</html>
"""


def trend_arrow(t):
    return {"up": "▲升溫", "down": "▼降溫"}.get(t, "－持平")


def flames_for(symbol: str, flags: dict) -> list[str]:
    tags = []
    for key in ("fx", "cb", "sd"):
        if symbol in flags.get(f"{key}_topn", []):
            tags.append(key)
    return tags


def render_index(radar: dict) -> str:
    rows = []
    for ind in radar.get("industries", []):
        cls = "up" if ind["trend"] == "up" else ("down" if ind["trend"] == "down" else "")
        rows.append(f"""
<a class="card" href="industry/{esc(ind['id'])}.html">
  <div class="rank">第 {ind['rank']} 名</div>
  <div class="name">{esc(ind['name'])}</div>
  <div class="heat-row">
    <div class="heat-bar"><i style="width:{ind['heat_score']}%"></i></div>
    <div class="heat-score">{ind['heat_score']}</div>
  </div>
  <div class="trend {cls}">{trend_arrow(ind['trend'])}　{len(ind['stocks'])} 檔個股</div>
</a>""")
    body = f"""
<div class="market-summary">{esc(radar.get('market_summary', ''))}</div>
<div class="updated">產業熱度更新時間：{esc(radar.get('generated_at', '—'))}</div>
<div class="grid-cards">{''.join(rows)}</div>
"""
    return page("台股產業熱度雷達", body, depth=0)


def render_industry(ind: dict, names: dict, prices: dict, flags: dict) -> str:
    why = "".join(f"<li>{esc(w)}</li>" for w in ind.get("why_hot", []))
    stock_rows = []
    for sym in ind["stocks"]:
        p = prices.get(sym)
        name = names.get(sym, "")
        flame_keys = flames_for(sym, flags)
        flame_html = "🔥" * len(flame_keys) if flame_keys else "－"
        if p:
            bars = p["bars"]
            last = bars[-1][4]
            prev = bars[-2][4] if len(bars) > 1 else last
            chg = (last / prev - 1) * 100 if prev else 0
            chg_cls = "up" if chg >= 0 else "down"
            price_html = f'{last:.2f}</td><td class="price-chg {chg_cls}">{chg:+.2f}%'
            link_open, link_close = f'<a href="../stock/{esc(sym)}.html">', "</a>"
        else:
            price_html = "—</td><td>—"
            link_open = link_close = ""
        stock_rows.append(f"""
<tr>
  <td>{link_open}{esc(sym)}{link_close}</td>
  <td>{link_open}{esc(name)}{link_close}</td>
  <td>{price_html}</td>
  <td class="flames">{flame_html}</td>
</tr>""")
    body = f"""
<div class="breadcrumb"><a href="../index.html">首頁</a> ＞ {esc(ind['name'])}</div>
<h2>{esc(ind['name'])}　<span class="heat-score">熱度 {ind['heat_score']}／第 {ind['rank']} 名</span></h2>
<p class="trend">{trend_arrow(ind['trend'])}</p>
<div class="market-summary">
  {esc(ind.get('summary', ''))}
  <ul>{why}</ul>
</div>
<table class="stocklist">
<thead><tr><th>代號</th><th>名稱</th><th>收盤</th><th>漲跌</th><th>🔥火焰</th></tr></thead>
<tbody>{''.join(stock_rows)}</tbody>
</table>
"""
    return page(f"{ind['name']} － 台股產業熱度雷達", body, depth=1)


def render_stock(sym: str, name: str, p: dict, industries_of: list[dict], flags: dict) -> str:
    flame_keys = flames_for(sym, flags)
    ind_links = "、".join(
        f'<a href="../industry/{esc(i["id"])}.html">{esc(i["name"])}</a>' for i in industries_of
    ) or "（不在鄧哥雷達的分類裡）"

    if flame_keys:
        items = "".join(f"<li>{esc(STRAT_LABEL[k])}</li>" for k in flame_keys)
        flame_block = f"""
<div class="flame-panel">
  <span class="flames-big">{"🔥" * len(flame_keys)}</span>目前符合 {len(flame_keys)} 個已建立的選股條件：
  <ul>{items}</ul>
</div>"""
    else:
        flame_block = '<div class="no-flame">目前沒有符合任何已建立的選股條件（外資／combo／自營自行）。</div>'

    last = p["last_close"]
    last_date = p["last_date"]
    payload = json.dumps(
        {"dates": p["dates"], "bars": p["bars"], "vol": p["vol"], "ma": p["ma"]},
        ensure_ascii=False, allow_nan=False,
    )
    body = f"""
<div class="breadcrumb"><a href="../index.html">首頁</a> ＞ {ind_links} ＞ {esc(sym)}</div>
<div class="stock-head">
  <span class="symbol">{esc(sym)}</span>
  <span class="name">{esc(name)}</span>
  <span class="last-close">{last:.2f}　<span class="updated">（{esc(last_date)} 收盤）</span></span>
</div>
<div class="industries-of">所屬產業：{ind_links}</div>
{flame_block}
<div id="chart"></div>
<div class="legend">
  <span><i style="background:#b39dff"></i>MA5</span>
  <span><i style="background:#ffd54f"></i>MA20</span>
  <span><i style="background:#25e6ff"></i>MA60</span>
  <span><i style="background:#ff5277"></i>紅漲</span>
  <span><i style="background:#2ee6a8"></i>綠跌</span>
</div>
<script src="../assets/lightweight-charts.standalone.production.js"></script>
<script src="../assets/chart.js"></script>
<script>
  RadarChart.render(document.getElementById('chart'), {payload});
</script>
"""
    return page(f"{name}（{sym}） － 台股產業熱度雷達", body, depth=1)


def build():
    radar = load_json(DATA / "radar.json", {"industries": [], "all_stocks": [], "market_summary": ""})
    names = load_json(DATA / "names.json", {})
    flags = load_json(DATA / "flags.json", {})

    stock_to_industries: dict[str, list[dict]] = {}
    for ind in radar.get("industries", []):
        for sym in ind["stocks"]:
            stock_to_industries.setdefault(sym, []).append(ind)
    for sym, lst in stock_to_industries.items():
        lst.sort(key=lambda i: i["rank"])

    prices = {}
    for sym in radar.get("all_stocks", []):
        pf = DATA / "prices" / f"{sym}.json"
        if pf.exists():
            prices[sym] = json.loads(pf.read_text(encoding="utf-8"))

    (DOCS / "index.html").write_text(render_index(radar), encoding="utf-8")

    ind_dir = DOCS / "industry"
    ind_dir.mkdir(parents=True, exist_ok=True)
    for ind in radar.get("industries", []):
        (ind_dir / f"{ind['id']}.html").write_text(
            render_industry(ind, names, prices, flags), encoding="utf-8"
        )

    stock_dir = DOCS / "stock"
    stock_dir.mkdir(parents=True, exist_ok=True)
    n_stock = 0
    for sym, p in prices.items():
        name = names.get(sym, sym)
        (stock_dir / f"{sym}.html").write_text(
            render_stock(sym, name, p, stock_to_industries.get(sym, []), flags), encoding="utf-8"
        )
        n_stock += 1

    print(f"[build_site] index.html + {len(radar.get('industries', []))} 產業頁 + {n_stock} 個股頁")


if __name__ == "__main__":
    build()
