# marathon

台灣馬拉松報名資訊總覽，提供地點、時間與報名狀態篩選，並彙整多個賽事來源。

## 使用方式

### 啟動靜態網站

```bash
python -m http.server 8000
```

開啟 <http://localhost:8000> 即可查看。

### 更新賽事資料

1. 安裝依賴：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 執行爬蟲：

```bash
python scripts/fetch_events.py --output data/events.json
```

> 各網站的 HTML 結構可能會調整，若抓取失敗請更新 `scripts/fetch_events.py` 的 CSS selector。
