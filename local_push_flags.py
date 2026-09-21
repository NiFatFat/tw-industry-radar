# -*- coding: utf-8 -*-
r"""在本機用雪鴞算「現在」三套策略（外資／combo／自營自行）的前15名，
寫成小檔案 docs/data/flags.json，然後 git push 上雲端 repo。

⛔ 帳號密碼全程留在本機（雪鴞 .env），這支腳本只把「前15名是哪幾檔股票代號」
   這種完全不敏感的小結果推上去，雲端網站（GitHub Actions）只讀這個檔、不重算。

沿用 dashboard/pit_picks.py 的三支函式，規則逐字不變：
  picks_foreign     外資40日買超÷發行張數，前15檔
  picks_self_dealer 自營自行40日買超÷發行張數，前15檔（⚠️觀察中，非已驗證策略）
  picks_combo       營收YoY×創新高各前20%，綜合排名前15檔

用法：雙擊同資料夾的「更新火焰標記.bat」
"""
from __future__ import annotations
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
STUDENT_PACK = HERE.parent                       # E:\Downloads\學員包
ENV = str(STUDENT_PACK / ".env")

sys.path.insert(0, str(STUDENT_PACK / "skills" / "snowyowl" / "scripts"))
sys.path.insert(0, str(STUDENT_PACK / "dashboard"))

from owl_login import login          # noqa: E402
import pit_picks                     # noqa: E402

FLAGS_OUT = HERE / "docs" / "data" / "flags.json"


def main():
    print(">>> 登入雪鴞、算三套策略目前的前15名...")
    api = login(ENV)
    today = dt.date.today()

    fx, fx_t = pit_picks.picks_foreign(api, today)
    sd, sd_t = pit_picks.picks_self_dealer(api, today)
    cb, cb_t = pit_picks.picks_combo(api, today)

    out = {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "fx_signal_date": str(fx_t.date()) if fx_t is not None else None,
        "sd_signal_date": str(sd_t.date()) if sd_t is not None else None,
        "cb_signal_date": str(cb_t.date()) if cb_t is not None else None,
        "fx_topn": [r["symbol"] for r in fx],
        "sd_topn": [r["symbol"] for r in sd],
        "cb_topn": [r["symbol"] for r in cb],
    }
    FLAGS_OUT.parent.mkdir(parents=True, exist_ok=True)
    FLAGS_OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")

    print(f"外資 {len(out['fx_topn'])} 檔　combo {len(out['cb_topn'])} 檔　自營自行 {len(out['sd_topn'])} 檔")
    print(f"已寫入：{FLAGS_OUT}")

    _git_push()


def _git_push():
    def run(*args):
        return subprocess.run(["git", *args], cwd=HERE, check=False,
                               capture_output=True, text=True, encoding="utf-8")

    r = run("status", "--porcelain", "docs/data/flags.json")
    if not r.stdout.strip():
        print("flags.json 內容跟上次 push 的一樣，不用重推。")
        return

    run("add", "docs/data/flags.json")
    msg = f"更新火焰標記 {dt.date.today().isoformat()}"
    c = run("commit", "-m", msg)
    print(c.stdout.strip() or c.stderr.strip())
    p = run("push")
    if p.returncode != 0:
        print("⚠ git push 失敗，內容如下（可能是還沒設定遠端 repo，或要先手動 push 一次做認證）：")
        print(p.stderr.strip())
    else:
        print("已推上雲端 repo，等 GitHub Actions 跑完就會出現在網站上。")


if __name__ == "__main__":
    main()
