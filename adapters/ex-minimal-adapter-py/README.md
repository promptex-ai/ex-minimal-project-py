# ex-minimal-adapter-py

[ex-minimal-project-py](../../) 的 adapter 擴展。由專案以路徑來源（`[tool.uv.sources]` 的 editable path）掛上：Python 的 import 走發布名對應的 import 套件名，帶連字號的目錄無法直接 import；同時保持可發布形態——中繼欄位、參數宣告與授權都隨套件出貨，版號是 1.0.0 正式版。

適配以 SDK 層實作，只用 `AdapterContext` 的公開介面。`emit` 的責任鏈固定四步：

1. 算落點表——渲染要靠它解析引用，因此必須在渲染之前完成。
2. 回報不支援的 kind——逐一列進報告，不靜默丟棄。
3. 渲染並產出節點——平台缺某機制時記 degrade 降級。
4. 產出被引用的資源。

本適配示範的平台只有提示詞單檔與參考資料：支援 skill、rule、instruction，不支援 agent、hook、mcp、permission。適配綁語言——同一個平台要服務另兩個生態的專案時，各自以該語言的 SDK 實作一份。

## 在本專案的接法

`promptex.config.py` 的目標清單寫成 `targets=[claude(), ex_minimal_adapter()]`，claude 是內建適配、本擴展是第三方適配，同一份源碼因此投影出兩套平台原生產物。跑 `uv run promptex build --install .` 後產物落在 `.ex-minimal-adapter-py/prompts/`，安裝報告會列出一項降級：範例規則宣告了適用範圍，而本平台無範圍載入機制，改為常駐並在內文標註適用範圍。

## 參數宣告

參數宣告（標準 JSON Schema）住import 套件目錄裡的 `promptex.config.schema.json`，由 `__init__.py` 自己讀進來，隨中介表示交給讀取端；`promptex config declare ex-minimal-adapter-py` 讀的是同一份檔案。

## 發布

發布走專案的發布流程（Trusted Publishing），不在套件目錄手動發布，步驟見專案根 [README 的「發布」一節](../../README.md#發布)。

版號 `1.0.0` 是正式版，與 npm、crates.io 側逐字相同。安裝端照一般寫法即可：`pip install ex-minimal-adapter-py`（或 `uv pip install ex-minimal-adapter-py`），不需要 `--pre`。

SDK 依賴是 `dependencies` 的 `promptex-py`，指向 registry 上正式發布的版本。發布驗證、消費端安裝與實際執行用的都是同一份 SDK。

名稱刻意不帶 `promptex-adapter-` 前綴——那是給要被消費端搜尋到的套件用的；本擴展的定位是示範，改以 keywords 的 `promptex-adapter` 承載可搜尋性。
