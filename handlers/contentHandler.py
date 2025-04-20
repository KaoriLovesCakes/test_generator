import importlib.util
import json
import os
import random
import re
import shutil

import dotenv
import soundfile as sf
from PIL import Image
from rich import print

dotenv.load_dotenv()

# https://github.com/gpoore/text2qti/blob/master/text2qti/quiz.py
# For generating DOCX file. Syntaxes outside these are currently not supported.
QUESTION_PATTERN = r"^\d+\."
ANSWER_PATTERNS = {
    "mctf": r"^\*?[a-zA-Z]\)",
    "multans": r"^\[\*?\s?\]",
    "shortans": r"^\*",
}
SOLUTION_PATTERN = r"^\!"
ANSWER_OR_SOLUTION_PATTERN = "|".join(
    f"({p})" for p in list(ANSWER_PATTERNS.values()) + [SOLUTION_PATTERN]
)
MEDIA_PATTERN = r"^\!\[[^\]]*\]\([^\)]+\)"
MEDIA_COMPONENTS_PATTERN = r"!\[([^\]]*)\]\(([^)]+)\)"

IMAGE_FORMATS = ["gif", "jpeg", "jpg", "svg", "png"]
AUDIO_FORMATS = ["mp3", "mpeg"]


def load_handler(handler_name: str):
    handler_path = os.path.join("handlers/custom", f"{handler_name}.py")

    if not os.path.exists(handler_path):
        raise ImportError(f"Module {handler_name} not found at {handler_path}.")

    module_name = f"handlers.custom.{handler_name.replace('/', '.')}"

    spec = importlib.util.spec_from_file_location(module_name, handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "handler"):
        raise ImportError(f"Module {handler_name} does not define function handler.")

    return module.handler


def txt_to_json(content: str):
    problems = {}

    for i, problem_raw in enumerate(
        re.split(QUESTION_PATTERN, content, flags=re.MULTILINE)[1:]
    ):
        chunks = [
            chunk.strip()
            for chunk in re.split(
                ANSWER_OR_SOLUTION_PATTERN, problem_raw, flags=re.MULTILINE
            )
            if chunk
        ]

        answers = []
        solution = ""
        for j in range(1, len(chunks), 2):
            prefix, content = chunks[j], chunks[j + 1]
            if re.match(SOLUTION_PATTERN, prefix):
                solution = content
            else:
                answers.append((prefix, content))
        medias = []
        for media_raw in [
            line.strip()
            for line in chunks[0].splitlines()
            if re.match(MEDIA_PATTERN, line.strip())
        ]:
            _, media_path = re.search(MEDIA_COMPONENTS_PATTERN, media_raw).groups()
            medias.append(media_path)
        question = re.sub(MEDIA_PATTERN[1:], "", chunks[0]).strip()

        problems[f"q{i + 1}"] = {
            "question": question,
            "answers": answers,
            "solution": solution,
            "medias": medias,
        }

    return problems


def json_to_txt(problems: dict, path):
    if not problems:
        return ""

    indent_size = max(len(str(len(problems))) + 2, 6)

    def _get_formatted_multiline_str(p: str, s: str):
        if not s:
            return ""
        stripped_lines = [line.strip() for line in s.splitlines()]
        formatted_lines = [
            f"{' ' * indent_size}{line}" if line else "" for line in stripped_lines
        ]
        formatted_lines[0] = p.ljust(indent_size) + stripped_lines[0]
        return "\n".join(formatted_lines)

    content = ""

    if path:
        assets_dir = os.path.join(path, "assets")
        os.makedirs(assets_dir, exist_ok=True)

    n_problems = 0

    for key, problem in problems.items():
        if "raw" in problem:
            content += problem["raw"] + "\n\n"
            continue

        if "text" in problem:
            content += _get_formatted_multiline_str("Text: ", problem["text"]) + "\n\n"
            continue

        n_problems += 1

        question = problem["question"]
        solution = problem["solution"]
        answers = problem["answers"]
        medias = problem["medias"]

        for j, media_loc in enumerate(medias):
            media_format = os.path.splitext(media_loc)[1][1:]

            if os.path.isfile(media_loc):
                if path:
                    if media_format in IMAGE_FORMATS:
                        img = Image.open(media_loc)
                        media_path = os.path.join(
                            assets_dir,
                            f"{key}_{j}.png",
                        )
                        img.save(media_path)
                    elif media_format in AUDIO_FORMATS:
                        data, samplerate = sf.read(media_loc)
                        media_path = os.path.join(
                            assets_dir,
                            f"{key}_{j}.mp3",
                        )
                        sf.write(media_path, data, samplerate)
                    else:
                        raise Exception(f"Invalid or unsupported media at: {media_loc}")
                question += f"\n\n![{key}_{j}]({os.path.abspath(media_loc)})"
            else:
                raise Exception(f"Invalid or unsupported media at: {media_loc}")

        content += _get_formatted_multiline_str(f"{n_problems}.", question) + "\n\n"
        if solution:
            content += _get_formatted_multiline_str("!", solution) + "\n\n"
        for prefix, answer in answers:
            content += _get_formatted_multiline_str(prefix, answer) + "\n\n"

    return content


def content_handler(path: str, config_global: dict, config_per_prompt: dict):
    content_dir = os.path.join(path, "content.txt")
    logs_dir = os.path.join(path, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    problems = {}
    n_prompts = len(config_per_prompt)
    for i, (key, config_per_prompt_curr) in enumerate(config_per_prompt.items()):
        print((f"[blue]├── [/blue][yellow]Đang xử lí batch {i + 1}/{n_prompts}..."))

        problems_curr = {}

        if config_per_prompt_curr["mode"] == "manual":
            with open(config_per_prompt_curr["source"], "r", encoding="utf-8") as f:
                problems_curr = txt_to_json(f.read())

            print(
                (
                    "[blue]│   └── [/blue]"
                    + f"[green]Đã đọc nội dung đề thi tại [white]{content_dir}[/white] thành công.[/green]"
                )
            )

        if config_per_prompt_curr["mode"] == "generated":
            prompt_name = config_per_prompt_curr["prompt"]

            prompt_dir = os.path.join("prompts", prompt_name)
            prompt_copy_dir = os.path.join(path, prompt_dir)
            os.makedirs(os.path.dirname(prompt_copy_dir), exist_ok=True)
            shutil.copy(prompt_dir, os.path.join(path, prompt_dir))

            problems_curr = {}

            front_handler = load_handler(config_per_prompt_curr["handler"])
            n_problems = config_per_prompt_curr["n_problems"]

            with open(prompt_dir, "r", encoding="utf-8") as f:
                prompt_content = f.read()

            problems_curr, response = front_handler(prompt_content, n_problems)

            content_curr_dir = os.path.join(logs_dir, f"{key}_content.txt")
            with open(content_curr_dir, "w+", encoding="utf-8") as f:
                f.write(json_to_txt(problems_curr, None))

            try:
                json.loads(response)
                response_dir = os.path.join(logs_dir, f"{key}_response.json")
                with open(response_dir, "w+", encoding="utf-8") as f:
                    f.write(response)
            except Exception:
                response_dir = os.path.join(logs_dir, f"{key}_response.rxt")
                with open(response_dir, "w+", encoding="utf-8") as f:
                    f.write(response)

            print(
                (
                    "[blue]│   └── [/blue]"
                    + f"[green]Đã đọc nội dung đề thi được sinh bởi prompt [white]{prompt_name}[/white] thành công.[/green]"
                )
            )

        problems.update(
            {f"{key}_{_key}": _value for _key, _value in problems_curr.items()}
        )

    do_shuffle = config_global.get("shuffle", False)
    if do_shuffle:
        problems_items = list(problems.items())
        random.shuffle(problems_items)
        problems = dict(problems_items)

    with open(content_dir, "w+", encoding="utf-8") as f:
        f.write(json_to_txt(problems, path))

    print(
        (
            "[blue]└── [/blue]"
            "[green]Đã tạo nội dung đề thi định dạng QTI-compatible thành công: [/green]"
            f"[white]{content_dir}[/white]"
        )
    )
