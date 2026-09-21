# -*- coding: utf-8 -*-
r"""用 FinMind 免費 API 抓 radar.json 裡每一檔股票的日K，算 5/20/60 MA，
輸出給 tv-chart 用的緊湊格式：docs/data/prices/{symbol}.json

⛔ 只在雲端（GitHub Actions）用這支，不是全市場選股，只是抓 93 檔股票的股價
   拿來畫圖，跟本機雪鴞算的 flags.json（三套策略的全市場前15名）是兩件事。

Token 來源：環境變數 FINMIND_TOKEN（GitHub Actions 的 secrets），
本機測試則從 ..\..\.env 讀 FINMIND_TOKEN（沿用 finmind skill 的讀法，不印值）。
"""
from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.parse
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RADAR = ROOT / "docs" / "data" / "radar.json"
OUT_DIR = ROOT / "docs" / "data" / "prices"
NAMES_OUT = ROOT / "docs" / "data" / "names.json"

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
LOOKBACK_DAYS_CALENDAR = 560   # 抓到足夠算 60MA + 留約一年圖表視窗的日曆天數
MA_WINDOWS = (5, 20, 60)


def _load_token() -> str:
    tok = os.environ.get("FINMIND_TOKEN")
    if tok:
        return tok.strip()
    env_path = ROOT.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("FINMIND_TOKEN="):
                return line.strip().split("=", 1)[1].strip()
    raise RuntimeError("找不到 FINMIND_TOKEN（環境變數或 .env 都沒有）")


def _get(dataset: str, data_id: str, start: str, token: str) -> list[dict]:
    params = {"dataset": dataset, "data_id": data_id, "start_date": start}
    url = FINMIND_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.loads(r.read().decode("utf-8"))
    if payload.get("status") != 200:
        raise RuntimeError(f"FinMind {dataset} {data_id} 失敗：{payload.get('msg')}")
    return payload.get("data", [])


def _round(x):
    return None if x is None else round(float(x), 3)


def build_symbol(symbol: str, token: str, start: str) -> dict | None:
    rows = _get("TaiwanStockPrice", symbol, start, token)
    if not rows:
        return None
    rows.sort(key=lambda r: r["date"])
    dates = [r["date"] for r in rows]
    closes = [float(r["close"]) for r in rows]
    opens = [float(r["open"]) for r in rows]
    highs = [float(r["max"]) for r in rows]
    lows = [float(r["min"]) for r in rows]
    vols = [float(r.get("Trading_Volume") or 0) for r in rows]  # 股 → 之後換算成張

    n = len(closes)
    ma = {w: [None] * n for w in MA_WINDOWS}
    run_sum = {w: 0.0 for w in MA_WINDOWS}
    for w in MA_WINDOWS:
        for i in range(n):
            run_sum[w] += closes[i]
            if i >= w:
                run_sum[w] -= closes[i - w]
            if i >= w - 1:
                ma[w][i] = run_sum[w] / w

    warm = max(w for w in MA_WINDOWS) - 1  # 60MA 準備好之前的天數整段丟掉，避免 NaN
    if n <= warm:
        return None

    bars = []
    vol = []
    for i in range(warm, n):
        yang = closes[i] >= opens[i]
        color_idx = 0 if yang else 1
        bars.append([i - warm, round(opens[i], 2), round(highs[i], 2), round(lows[i], 2), round(closes[i], 2), color_idx])
        vol.append([i - warm, round(vols[i] / 1000, 1), 0 if yang else 1])

    ma_lines = {}
    for w in MA_WINDOWS:
        ma_lines[str(w)] = [[i - warm, _round(ma[w][i])] for i in range(warm, n)]

    return {
        "symbol": symbol,
        "dates": dates[warm:],
        "bars": bars,
        "vol": vol,
        "ma": ma_lines,
        "last_close": closes[-1],
        "last_date": dates[-1],
    }


def load_stock_names(symbols: list[str], token: str) -> dict:
    """股票代號 → 中文名稱，用 TaiwanStockInfo 一次查全部再篩選（比逐檔查省額度）。"""
    try:
        params = {"dataset": "TaiwanStockInfo"}
        url = FINMIND_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            payload = json.loads(r.read().decode("utf-8"))
        rows = payload.get("data", [])
    except Exception as e:
        print(f"[fetch_prices] 抓股票名稱失敗：{e}")
        return {}
    want = set(symbols)
    names = {}
    for row in rows:
        sid = row.get("stock_id")
        if sid in want and sid not in names:
            names[sid] = row.get("stock_name")
    return names


def build():
    radar = json.loads(RADAR.read_text(encoding="utf-8"))
    symbols = radar.get("all_stocks", [])
    token = _load_token()
    start = (dt.date.today() - dt.timedelta(days=LOOKBACK_DAYS_CALENDAR)).isoformat()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ok, failed = 0, []
    for i, sym in enumerate(symbols):
        try:
            data = build_symbol(sym, token, start)
        except Exception as e:
            failed.append((sym, str(e)))
            data = None
        if data is None:
            failed.append((sym, "no data / 暖機天數不足"))
            continue
        (OUT_DIR / f"{sym}.json").write_text(
            json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8"
        )
        ok += 1
        if (i + 1) % 20 == 0:
            time.sleep(1)  # 溫和一點，避免瞬間打爆免費額度的速率限制

    names = load_stock_names(symbols, token)
    NAMES_OUT.write_text(json.dumps(names, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")

    print(f"[fetch_prices] 成功 {ok}/{len(symbols)} 檔，失敗 {len(failed)} 檔")
    for sym, msg in failed[:20]:
        print(f"  - {sym}: {msg}")


if __name__ == "__main__":
    build()
