# 台股產業熱度雷達（雲端版）

首頁看產業熱度排行 → 點產業看裡面有哪些個股 → 點個股看日K線圖（5MA/20MA/60MA＋成交量）。
再疊加自家三套選股策略當「🔥火焰標記」：一檔股票現在符合幾套策略，就打幾個火焰（最多3個）。

## 這個網站怎麼運作

```
duang0615/tw-market-radar ──┐
 （產業熱度、產業→個股對照）  │
                            ├─→ GitHub Actions（每天收盤後自動跑）──→ 網頁（GitHub Pages）
FinMind 免費 API ───────────┘        產業頁 + 個股K線圖

你的電腦（雪鴞，全市場~1800檔）
 外資/combo/自營自行 前15名  ──→ 你雙擊「更新火焰標記.bat」──→ 推一個小檔案上 GitHub
```

**為什麼火焰標記要分開來、從本機推**：三套策略的「前15名」要在全市場~1800檔股票裡選才準，
這件事雪鴞在本機做（帳密全程留在 `.env`，不上雲端）。雲端 GitHub Actions 完全不碰雪鴞，
只做兩件輕量的事：抓鄧哥的產業熱度資料、用 FinMind 免費額度抓 93 檔股票的股價畫K線圖。

## 檔案說明

| 檔案 | 做什麼 | 在哪裡跑 |
|---|---|---|
| `pipeline/fetch_radar.py` | 抓鄧哥 tw-market-radar 的產業熱度 | GitHub Actions |
| `pipeline/fetch_prices.py` | FinMind 抓93檔股價、算均線 | GitHub Actions |
| `pipeline/build_site.py` | 組出 `docs/` 底下所有網頁 | GitHub Actions（也可以自己本機跑測試） |
| `local_push_flags.py` | 雪鴞算三套策略前15名，寫 `flags.json` 並 push | **只能本機跑**（要雪鴞帳密） |
| `更新火焰標記.bat` | 雙擊執行上面那支 | 你的電腦 |

## 什麼時候雙擊「更新火焰標記.bat」

外資／自營自行策略每月換股一次（月初第一個交易日），combo 策略每月10、11號換股。
其他時間火焰標記不會變，不用天天跑，每月這兩個時間點跑一次就好。

## 部署到 GitHub（第一次設定）

1. GitHub 開一個新的 **public** repo（public 才有免費、無限額度的 Pages + Actions）
2. 這個資料夾 `git remote add origin <你的repo網址>`，push 上去
3. Repo → Settings → Pages → Source 選「Deploy from a branch」→ branch=`main`、資料夾=`/docs`
4. Repo → Settings → Secrets and variables → Actions → New repository secret
   → 名稱 `FINMIND_TOKEN`，值貼上你自己的 FinMind API token
5. Repo → Actions 分頁，手動觸發一次「更新產業熱度雷達網站」workflow，確認會成功跑完

## ⚠️ 使用前一定要知道的事

- **產業熱度**是鄧哥 tw-market-radar 的「過去72小時」即時快照，不是歷史趨勢，不能拿來回測，
  也**沒有驗證過**「熱門產業的股票之後會不會漲比較多」。
- **🔥火焰標記**代表這檔股票「現在」符合哪些自家選股條件，不是投資建議、不是目標價、
  不保證任何報酬。**自營自行策略目前只是觀察紀錄**（IC t值僅1.49，樣本4年，還沒驗證穩定），
  不是像外資、combo 那樣已經驗證過的策略。
- K線圖股價資料來自 FinMind 免費 API，收盤價 EOD 更新，不是即時報價。

本網站僅供 AI 工具應用教學，不提供任何投資建議、不推薦任何個股、不保證任何投資績效。
投資有風險，請謹慎評估並自負盈虧。
