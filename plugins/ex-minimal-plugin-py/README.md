# ex-minimal-plugin-py

[ex-minimal-project-py](../../) 的 plugin 擴展。由專案以路徑來源（`[tool.uv.sources]` 的 editable path）掛上：Python 的 import 走發布名對應的 import 套件名，帶連字號的目錄無法直接 import；同時保持可發布形態——中繼欄位、參數宣告與授權都隨套件出貨，版號比照 promptex 的 alpha 原型套件。

plugin 掛在求值管線的三個生命週期上，順序固定：

1. `prepare`——唯一 async 的階段，跑在收集遍之前。真實 plugin 在這裡請求外部資源，或以 `ctx.cacheDir` 快取、`ctx.writeLock` 記錄鎖定，再經閉包把資料交給後續階段。
2. `transform`——改寫遍。改寫既有節點一律經 ctx 操作函式（`appendContent`／`patchConfig`），型別安全、變更可追蹤、衝突可偵測；也可在此以 `define*` 新增節點。
3. `validate`——解析遍，核心檢查在先。對註冊表做結構驗證並回傳診斷，空清單即通過。

plugin 產出的是節點而非檔案：要落地的內容以 `define*` 新增資源節點，由核心落地為產物。

## 在本專案的接法

`promptex.config.py` 以 `plugins=[create_plugin()]` 掛上。跑 `uv run promptex install .` 後，兩個平台的 `example-rule` 產物末尾都會多出本 plugin 在 `transform` 追加的那一行——那是它有生效的可見證據。

## 參數宣告

參數宣告（標準 JSON Schema）住import 套件目錄裡的 `promptex.config.schema.json`，由 `__init__.py` 自己讀進來，隨中介表示交給讀取端；`promptex config declare ex-minimal-plugin-py` 讀的是同一份檔案。

## 發布

```bash
uv build
uvx twine check dist/*
uv publish
```

版號寫 PEP 440 的 `0.0.1a1`，與另兩個生態的 `0.0.1-alpha.1` 指同一個版本——三生態版號無法逐字相同，這是預發布版號的既有限制。安裝端要 `pip install --pre ex-minimal-plugin-py`：預發布版號不會被 pip 預設選中。

SDK 依賴不必換：`dependencies` 的 `promptex-py~=0.0.0` 在 registry 上對到的是 promptex-prototype 發的 `0.0.0` **介面樁**——型別與簽名逐字複製正式版、方法本體一律拋錯。發布驗證（尤其 `cargo publish` 的建置）拿它編得過；裝到消費端也裝得起來，但實際執行要靠工作區覆寫指向本地的正式版 SDK，否則第一個碰到樁的呼叫就會以「promptex 介面樁」開頭的錯誤中止。

名稱刻意不帶 `promptex-plugin-` 前綴——那是給要被消費端搜尋到的套件用的；本擴展的定位是示範，改以 keywords 的 `promptex-plugin` 承載可搜尋性。
