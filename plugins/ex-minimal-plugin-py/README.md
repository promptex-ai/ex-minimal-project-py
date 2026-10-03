# ex-minimal-plugin-py

[ex-minimal-project-py](../../) 的 plugin 擴展。由專案以路徑來源（`[tool.uv.sources]` 的 editable path）掛上：Python 的 import 走發布名對應的 import 套件名，帶連字號的目錄無法直接 import；同時保持可發布形態——中繼欄位、參數宣告與授權都隨套件出貨，版號是 1.0.0 正式版。

plugin 掛在求值管線的三個生命週期上，順序固定：

1. `prepare`——唯一 async 的階段，跑在收集遍之前。真實 plugin 在這裡請求外部資源，或以 `ctx.cacheDir` 快取、`ctx.writeLock` 記錄鎖定，再經閉包把資料交給後續階段。
2. `transform`——改寫遍。改寫既有節點一律經 ctx 操作函式（`appendContent`／`patchConfig`），型別安全、變更可追蹤、衝突可偵測；也可在此以 `define*` 新增節點。
3. `validate`——解析遍，核心檢查在先。對註冊表做結構驗證並回傳診斷，空清單即通過。

plugin 產出的是節點而非檔案：要落地的內容以 `define*` 新增資源節點，由核心落地為產物。

## 在本專案的接法

`promptex.config.py` 以 `plugins=[create_plugin()]` 掛上。跑 `uv run promptex build --install .` 後，兩個平台的 `example-rule` 產物末尾都會多出本 plugin 在 `transform` 追加的那一行——那是它有生效的可見證據。

## 參數宣告

參數宣告（標準 JSON Schema）住import 套件目錄裡的 `promptex.config.schema.json`，由 `__init__.py` 自己讀進來，隨中介表示交給讀取端；`promptex config declare ex-minimal-plugin-py` 讀的是同一份檔案。

## 發布

發布走專案的發布流程（Trusted Publishing），不在套件目錄手動發布，步驟見專案根 [README 的「發布」一節](../../README.md#發布)。

版號 `1.0.0` 是正式版，與 npm、crates.io 側逐字相同。安裝端照一般寫法即可：`pip install ex-minimal-plugin-py`（或 `uv pip install ex-minimal-plugin-py`），不需要 `--pre`。

SDK 依賴是 `dependencies` 的 `promptex-py`，指向 registry 上正式發布的版本。發布驗證、消費端安裝與實際執行用的都是同一份 SDK。

名稱刻意不帶 `promptex-plugin-` 前綴——那是給要被消費端搜尋到的套件用的；本擴展的定位是示範，改以 keywords 的 `promptex-plugin` 承載可搜尋性。
