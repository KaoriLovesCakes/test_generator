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
        question = f"{problem['question']}\n\n"
        for j, image in enumerate(get_images(problem)):
            image_dir_relative = os.path.join(
                "assets",
                f"{key}_{j}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            )
            image_dir = os.path.join(path, image_dir_relative)
            image.save(image_dir)
            question += f"![{key}_{j}]({image_dir_relative})\n\n"
        content += f"{i + 1}. {_get_indented_multiline_str(question)}\n"

        ptype = problem["ptype"]

        if ptype == "multiple_choice":
            is_true = problem["is_true"]
            for j, choice in enumerate(problem["choices"]):
                choice_prefix = f"{'*' if j == is_true else ''}{'abcd'[j]})"
                content += f"{choice_prefix} {_get_indented_multiline_str(choice)}\n\n"

        if ptype == "true_false":
            is_true = problem["is_true"]
            for j, statement_pair in enumerate(problem["statements"]):
                statement = (
                    statement_pair["true"] if is_true[j] else statement_pair["false"]
                )
                statement_prefix = f"[{'*' if is_true[j] else ' '}]"
                content += (
                    f"{statement_prefix} {_get_indented_multiline_str(statement)}\n\n"
                )

        if ptype == "short_answer":
            answer = problem["answer"]
            content += f"* {answer}\n\n"

    return content
