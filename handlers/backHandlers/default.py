import os
from datetime import datetime


def get_images(problem):
    return []


def handler(content_dict: dict, path: str) -> str:
    """
    Takes in dict 'content_dict' where keys are the prompts and values are the respective LLM responses.
    Generates images under 'path' if needed.
    Returns text in QTI-compatible format.
    """

    def _get_indented_multiline_str(s: str):
        lines = [line.strip() for line in s.splitlines()]
        result = lines[0]
        for line in lines[1:]:
            result += f"\n        {line}"  # Should be enough
        return result

    content = ""

    for i, (key, problem) in enumerate(content_dict.items()):
        question = f"{problem['question']}"
        for j, image in enumerate(get_images(problem)):
            image_dir_relative = os.path.join(
                "assets",
                f"{key}_{j}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            )
            image_dir = os.path.join(path, image_dir_relative)
            image.save(image_dir)
            question += f"\n\n![{key}_{j}]({image_dir_relative})"

        ptype = problem["ptype"]

        if ptype == "multiple_choice":
            answer = problem["answer"]
            content += f"{i + 1}. {_get_indented_multiline_str(question)}\n\n"
            for j, choice in enumerate(problem["choices"]):
                choice_prefix = f"{'*' if j == answer else ''}{chr(ord('a') + j)})"
                content += f"{choice_prefix} {_get_indented_multiline_str(choice)}\n\n"

        if ptype == "true_false":
            answer = problem["answer"]
            for j, statement_pair in enumerate(problem["statements"]):
                statement = statement_pair["true" if answer[j] == "D" else "false"]
                statement_prefix = f"{chr(ord('a') + j)})"
                question += f"\n\n{statement_prefix} {statement}"
            content += f"{i + 1}. {_get_indented_multiline_str(question)}\n\n"
            content += f"* {answer}\n\n"

        if ptype == "short_answer":
            answer = problem["answer"]
            content += f"{i + 1}. {_get_indented_multiline_str(question)}\n\n"
            content += f"* {answer}\n\n"

    return content
