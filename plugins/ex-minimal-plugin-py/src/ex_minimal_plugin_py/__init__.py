"""最小可發布 plugin：三個生命週期各示範一件事，發布前把內容換成你的邏輯。

生命週期固定順序：prepare（唯一 async 的階段，收集遍之前）→ 源碼求值 →
transform（改寫遍）→ validate（解析遍，核心檢查在先）。plugin 產出的是
「節點」而非檔案：要落地的內容以 define_* 新增資源節點，由核心落地為產物。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from promptex import Diagnostic, Plugin

# 參數宣告（標準 JSON Schema）：由本套件自己讀進來、隨中介表示交給讀取端；
# `promptex config declare` 讀的是套件目錄裡的同一份檔案。
_SCHEMA = json.loads((Path(__file__).parent / "promptex.config.schema.json").read_text(encoding="utf-8"))

_DEFAULT_BANNER = "（本節點由 ex-minimal-plugin-py plugin 追加此行）"


def create_plugin(banner: Optional[str] = None) -> Plugin:
    # prepare 取得的資料存進閉包，transform 只讀閉包、不知道資料從何而來。
    resolved: list[str] = []

    async def _prepare(ctx) -> None:
        # 準備：唯一 async 的生命週期。真實 plugin 在這裡請求外部資源，或以
        # ctx.cache_dir 快取、ctx.write_lock 記錄鎖定；本範例只把參數收斂成
        # transform 要用的值。
        resolved[:] = [banner or _DEFAULT_BANNER]

    def _transform(ctx) -> None:
        # 改寫：改寫既有節點一律經 ctx 操作函式（append_content／patch_config），
        # 變更可追蹤、衝突可偵測；也可在此以 define_* 新增節點。
        for entry in ctx.entries:
            if entry.kind in ("skill", "rule"):
                ctx.append_content(entry, resolved[0])

    def _validate(ctx) -> list[Diagnostic]:
        # 驗證：對註冊表做結構驗證，回傳診斷（空清單即通過）。
        return [
            Diagnostic(
                code="ex-minimal-plugin-py-reserved-id",
                message=f"節點 {entry.id} 以保留前綴 promptex- 命名，請改用其他 id",
                at=[entry.at],
                severity="error",
            )
            for entry in ctx.entries
            if entry.id.startswith("promptex-")
        ]

    return Plugin(
        name="ex-minimal-plugin-py",
        # 宣告本擴充作用在哪幾種節點類型（供文件與讀取端），不隱含過濾。
        kinds=["skill", "rule"],
        # 相容的框架版本範圍：安裝的 promptex-py 落在範圍外時於編譯開始前報錯。
        version="^0.0.0",
        config_schema=_SCHEMA,
        prepare=_prepare,
        validate=_validate,
        transform=_transform,
    )
