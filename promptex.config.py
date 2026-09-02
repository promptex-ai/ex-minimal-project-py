from promptex import claude, define_config, unit

from ex_minimal_adapter_py import target as ex_minimal_adapter
from ex_minimal_plugin_py import create_plugin

# 兩個平台目標：claude 是內建適配，ex-minimal-adapter-py 是本專案自帶的第三方
# 適配，同一份源碼因此投影出兩套平台原生產物。plugin 在求值後的改寫遍追加內容，
# 兩個平台的產物都看得到它的痕跡。
config = define_config([
    unit(
        name="ex-minimal-project-py",
        src_dir="./prompts",
        out_dir=".",
        targets=[claude(), ex_minimal_adapter()],
        plugins=[create_plugin()],
    ),
])
