from promptex import claude, define_config, unit

config = define_config([
    unit(
        name="ex-minimal-project-py",
        src_dir="./prompts",
        out_dir=".",
        targets=[claude()],
    ),
])
