"""第三方 adapter：以 SDK 層實作，只用 AdapterContext 的公開介面。

emit 的責任鏈固定四步：① 算落點表 → ② 回報不支援的 kind → ③ 渲染並產出
節點（平台缺某機制時記 degrade 降級）→ ④ 產出被引用的資源。發布前把落點
規則與能力集合換成你的平台實況。

adapter 綁語言：本套件服務 Python 專案；TypeScript／Rust 專案要用同一個
平台時，各自以該語言的 SDK 實作一份。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from promptex import AdapterContext, DegradeItem, EmitFiles, define_target

# 參數宣告（標準 JSON Schema）：由本套件自己讀進來、隨中介表示交給讀取端；
# `promptex config declare` 讀的是套件目錄裡的同一份檔案。
_SCHEMA = json.loads((Path(__file__).parent / "promptex.config.schema.json").read_text(encoding="utf-8"))

# 平台能力：本範例只有提示詞單檔與參考資料，無代理、無事件機制。
_SUPPORTED = ("skill", "rule", "instruction")
_UNSUPPORTED = ("agent", "hook", "mcp", "permission")


def target(root: Optional[str] = None) -> dict:
    resolved_root = root or ".ex-minimal-adapter-py"

    def _node_path(entry) -> str:
        # 落點規則：提示詞一律單檔平鋪。
        return f"{resolved_root}/prompts/{entry.id}.md"

    def _resource_path(entry) -> str:
        # 資源集中於 refs/。
        return f"{resolved_root}/refs/{entry.id}.md"

    def _frontmatter(ctx: AdapterContext, entry) -> str:
        # 平台原生鍵的覆寫：一律經 ctx.overrides 讀取，不自己走
        # entry.config["platforms"]：「空物件視同未宣告」的判定與框架保留鍵
        # （promptex: 前綴）的過濾都由核心同一份實作承載，自己讀會各自重造
        # 而漂移。
        overrides = ctx.overrides(entry)
        if not overrides:
            return ""
        body = "\n".join(f"{k}: {v}" for k, v in overrides.items())
        return f"---\n{body}\n---\n\n"

    def _emit(ctx: AdapterContext) -> EmitFiles:
        # 型別標成 SDK 的 EmitFiles（值可為 str 或 bytes）而非 dict[str, str]：dict 的
        # 值型別不變（invariant），窄一格就指派不進 AdapterEmit。
        files: EmitFiles = {}

        # ① 先算落點表：渲染需要它解析引用，故必須在渲染之前完成。
        layout: dict[str, str] = {}
        for kind in _SUPPORTED:
            for e in ctx.entries(kind):
                layout[f"{kind}:{e.id}"] = _node_path(e)
        for kind in ("resource", "asset", "dir"):
            for e in ctx.entries(kind):
                layout[f"{kind}:{e.id}"] = _resource_path(e)

        # ② 不支援的 kind 逐一列報告，不靜默丟棄。
        for kind in _UNSUPPORTED:
            for e in ctx.entries(kind):
                ctx.unsupported(
                    DegradeItem(kind=kind, node_id=e.id, feature=kind, note=f"ex-minimal-adapter-py 無 {kind} 對應機制，該節點未產出")
                )

        # ③ 產出提示詞單檔；rule 的載入範圍在本平台無對應機制，降級為內文標註。
        for kind in _SUPPORTED:
            for e in ctx.entries(kind):
                path = _node_path(e)
                applies_to = (e.config or {}).get("appliesTo") or []
                note = ""
                if kind == "rule" and applies_to:
                    note = f"適用範圍：{'、'.join(applies_to)}\n\n"
                    ctx.degrade(
                        DegradeItem(
                            kind=kind,
                            node_id=e.id,
                            feature="scopedLoading",
                            note="ex-minimal-adapter-py 無範圍載入機制，改為常駐並於內文標註適用範圍",
                        )
                    )
                files[path] = f"{_frontmatter(ctx, e)}# {e.name}\n\n{note}{ctx.render(e, path, layout)}\n"

        # ④ 被引用的資源。
        for e in ctx.entries("resource"):
            path = _resource_path(e)
            files[path] = f"# {e.name}\n\n{ctx.render(e, path, layout)}\n"

        return files

    # 參數宣告隨 target 一起交給讀取端；`promptex config declare` 讀套件內的
    # 同一份 schema 檔。
    return define_target("ex-minimal-adapter-py", _emit, config_schema=_SCHEMA)
