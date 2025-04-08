import json
import os
from copy import deepcopy
from typing import List

import dotenv
import numpy as np
from google import genai
from pydantic import BaseModel, Field, create_model

dotenv.load_dotenv()

API_KEY = os.environ.get("API_KEY")
MODEL = os.environ.get("MODEL") or "gemini-2.0-flash"

client = genai.Client(api_key=API_KEY)

N_CHOICES = 4


class QuestionBlock(BaseModel):
    question: str = Field(
        ...,
        description="The question itself, providing context, numbers, events, etc.",
    )
    solution: str = Field(
        ...,
        description="Solution to the problem (with reasoning and calculation). Be detailed: What are the given info, what are the step by step reasonings.",
    )
    choice_true: str = Field(
        ...,
        description="A concise CORRECT answer. MUST BE CONSISTENT WITH THE SOLUTION ABOVE.",
    )
    choices_false: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="List of other choices, must be ALL WRONG",
    )


def handler(prompt_content: str, n_problems: int):
    """
    Takes in content of a prompt and the number of problems to be generated.
    Return LLM's response.
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt_content,
        config={
            "response_mime_type": "application/json",
            "response_schema": create_model(
                "MyQuestions",
                **{f"q{i}": (QuestionBlock, ...) for i in range(n_problems)},
            ),
            "temperature": 1.5,
        },
    ).text
    assert response is not None
    response_dict = json.loads(response)

    keys = response_dict.keys()

    problems = {
        key: dict.fromkeys(["ptype", "question", "answers", "medias"], None)
        for key in keys
    }

    for key in keys:
        problem_raw = response_dict[key]
        problem = problems[key]

        choices = deepcopy(problem_raw["choices_false"])
        i_correct = np.random.randint(N_CHOICES)
        choices.insert(i_correct, problem_raw["choice_true"])

        answers = []
        for i, choice in enumerate(choices):
            prefix = f"{'*' if i == i_correct else ''}{chr(ord('a') + i)})"
            answers.append((prefix, choice))

        problem["question"] = problem_raw["question"]
        problem["solution"] = problem_raw["solution"]
        problem["answers"] = answers
        problem["medias"] = []

    return (problems, response)
