import os
from datetime import datetime

import tomli
from clize import ArgumentError, run
from rich import print

from handlers import content_handler, docx_handler, qti_handler

CONFIG_FILE = "config.toml"
PROMPTS_DIR = "prompts"


def txt_to_docx(*, input: "i", output: "o" = None):
    """
    Generate exam content in docx format from QTI-compatible text format.

    :param input: Path to input file in QTI-compatible text format.
    :param output: Path to output. Will be created if not exists. (default: dist/{datetime})
    """

    if output is None:
        output = os.path.join("dist", datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(output)
    elif not os.path.isdir(output):
        raise ArgumentError(f"Not a directory: {output}")

    print("[yellow]Đang tạo file docx...[/yellow]")

    docx_handler(input, output)

    print(
        "[blue]└── [/blue]"
        "[green]Đã tạo file docx thành công: [/green]"
        f"[white]{os.path.join(output, 'exam.docx')}[/white]"
    )


def txt_to_qti(*, input: "i", output: "o" = None):
    """
    Generate exam in QTI format from QTI-compatible text format.

    :param input: Path to input file in QTI-compatible text format.
    :param output: Path to output. Will be created if not exists. (default: dist/{datetime})
    """

    if output is None:
        output = os.path.join("dist", datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(output)
    elif not os.path.isdir(output):
        raise ArgumentError(f"Not a directory: {output}")

    print("[yellow]Đang tạo file zip QTI...[/yellow]")

    qti_handler(input, output)

    print(
        "[blue]└── [/blue]"
        "[green]Đã tạo file zip QTI thành công: [/green]"
        f"[white]{os.path.join(output, 'qti.zip')}[/white]"
    )


def txt_to_docx_qti(*, input: "i", output: "o" = None):
    """
    Generate exam content in docx format, along with exam in QTI format, from QTI-compatible text format.

    :param input: Path to input file in QTI-compatible text format.
    :param output: Path to output. Will be created if not exists. (default: dist/{datetime})
    """

    if output is None:
        output = os.path.join("dist", datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(output)
    elif not os.path.isdir(output):
        raise ArgumentError(f"Not a directory: {output}")

    txt_to_docx(input=input, output=output)
    txt_to_qti(input=input, output=output)


def main(
    *,
    config: "c" = "config.toml",
    output: "o" = None,
    raw_content_only: "r" = False,
):
    """
    Generate a exam from LLM prompts.

    :param config: Path to config file.
    :param output: Path to output. Will be created if not exists. (default: dist/{datetime})
    :param raw_content_only: docx and QTI zip files will not be generated.
    """

    if output is None:
        output = os.path.join("dist", datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(output)
    elif not os.path.isdir(output):
        raise ArgumentError(f"Not a directory: {output}")

    with open(config, "r", encoding="utf-8") as log:
        config_all = tomli.loads(log.read())

    print(f"[green]Đã đọc config file tại [white]{config}[/white] thành công.[/green]")

    path = output
    if path == "":
        path = f"./dist/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not os.path.exists(path):
        os.makedirs(path)

    print(f"[green]Sẽ tạo đề thi tại [white]{path}[/white].[/green]")

    keys_per_prompt_generated = ["prompt", "handler"]
    keys_per_prompt_manual = ["source"]

    config_global = config_all.get("global", {})

    config_per_prompt = {}
    for i, config_per_prompt_curr in enumerate(config_all["batch"]):
        mode = ""
        if all((key in config_per_prompt_curr) for key in keys_per_prompt_generated):
            mode = "generated"
        if all((key in config_per_prompt_curr) for key in keys_per_prompt_manual):
            mode = "manual"

        if not mode:
            raise KeyError(f"Batch {i}: Insufficient keys.")

        if mode == "generated" and "n_problems" not in config_per_prompt_curr:
            config_per_prompt_curr["n_problems"] = 1

        config_per_prompt_curr["mode"] = mode
        config_per_prompt[f"batch_{i}"] = config_per_prompt_curr

    print("[yellow]Đang tạo nội dung đề thi...[/yellow]")

    content_handler(path, config_global, config_per_prompt)

    if raw_content_only:
        print("[green]File zip QTI và file docx sẽ không được tạo.[/green]")
    else:
        txt_to_docx_qti(
            input=os.path.join(path, "content.txt"), output=os.path.join(path)
        )


if __name__ == "__main__":
    run(main, alt=[txt_to_docx, txt_to_docx_qti, txt_to_qti])
