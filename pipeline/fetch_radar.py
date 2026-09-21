# -*- coding: utf-8 -*-
"""抓鄧哥（duang0615）tw-market-radar 的產業熱度資料。

跟 dashboard/industry_heat.py 抓法一樣，這裡只是把它變成雲端網站的資料層：
輸出 docs/data/radar.json，前端頁面（index.html / industry/*.html）直接讀這一份。

抓不到（沒網路、對方 repo 改版）不擋整條 pipeline，把上次的結果留著、
只在 meta.ok 標 False，前端可以顯示「熱度資料暫時取不到，顯示上次結果」。
"""
from __future__ import annotations
import json
import urllib.request
from pathlib import Path

INDUSTRIES_URL = "https://raw.githubusercontent.com/duang0615/tw-market-radar/main/data/industries.json"
RADAR_URL = "https://raw.githubusercontent.com/duang0615/tw-market-radar/main/data/radar.json"

OUT = Path(__file__).resolve().parent.parent / "docs" / "data" / "radar.json"


def fetch():
    with urllib.request.urlopen(INDUSTRIES_URL, timeout=20) as r:
        industries_def = json.loads(r.read().decode("utf-8"))
    with urllib.request.urlopen(RADAR_URL, timeout=20) as r:
        radar = json.loads(r.read().decode("utf-8"))
    return industries_def, radar


def build():
    try:
        industries_def, radar = fetch()
    except Exception as e:
        if OUT.exists():
            print(f"[fetch_radar] 抓取失敗（沿用舊資料）：{e}")
            return json.loads(OUT.read_text(encoding="utf-8"))
        raise

    heat_by_id = {ind["id"]: ind for ind in radar.get("industries", [])}
    def_by_id = {ind["id"]: ind for ind in industries_def}

    industries = []
    all_stocks = set()
    for ind_id, ind_def in def_by_id.items():
        h = heat_by_id.get(ind_id)
        if not h:
            continue
        stocks = ind_def.get("stocks", [])
        all_stocks.update(stocks)
        industries.append({
            "id": ind_id,
            "name": ind_def.get("name"),
            "group": ind_def.get("group"),
            "stocks": stocks,
            "heat_score": h.get("heat_score"),
            "rank": h.get("rank"),
            "trend": h.get("trend"),
            "why_hot": h.get("why_hot", []),
            "summary": h.get("summary"),
            "event_count": h.get("event_count"),
            "news_count": h.get("news_count"),
            "social_mentions": h.get("social_mentions"),
            "market_move": h.get("market_move"),
        })
    industries.sort(key=lambda x: (x["rank"] if x["rank"] is not None else 999))

    out = {
        "ok": True,
        "generated_at": radar.get("generated_at"),
        "market_summary": radar.get("market_summary"),
        "industries": industries,
        "all_stocks": sorted(all_stocks),
        "source": "https://github.com/duang0615/tw-market-radar",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")
    print(f"[fetch_radar] {len(industries)} 個產業、{len(all_stocks)} 檔股票 → {OUT}")
    return out


if __name__ == "__main__":
    build()
