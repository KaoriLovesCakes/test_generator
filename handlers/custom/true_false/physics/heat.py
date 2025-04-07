import json
import os
from tempfile import mkstemp
from typing import List

import dotenv
import matplotlib.pyplot as plt
import numpy as np
from google import genai
from pydantic import BaseModel, Field, create_model

dotenv.load_dotenv()

API_KEY = os.environ.get("API_KEY")
MODEL = os.environ.get("MODEL") or "gemini-2.0-pro-exp-02-05"

client = genai.Client(api_key=API_KEY)


class QuestionBlockVariables(BaseModel):
    event: List[str] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Array of names of current interval's event, like 'thêm đá vào', 'tăng công suất ấm',... If there's none, let it be empty ''. Note how there are 4 checkpoints, but 3 intervals.",
    )
    time: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Array of time values (in minutes). MUST BE SORTED AND STARTS WITH 0.",
    )
    temperature: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Array of temperature values in degree Celcius.",
    )


class StatementsPair(BaseModel):
    true: str = Field(
        ...,
        description="Think about the above carefully. Make sure that this statement MUST BE TRUE.",
    )
    false: str = Field(
        ...,
        description="This statement appears SIMILAR to the true one but MUST BE FALSE.",
    )


class QuestionBlock(BaseModel):
    context: str = Field(
        ...,
        description="The question's context. Keep it short.",
    )
    variables: QuestionBlockVariables = Field(
        ...,
        description="Certain variables in the problem. SHOULD BE CONSISTENT WITH THE INITIAL QUESTION ABOVE.",
    )
    question: str = Field(
        ...,
        description="The question itself, providing context, numbers, events, etc. MUST BE CONSISTENT WITH THE VARIABLES ABOVE.",
    )
    solution: str = Field(
        ...,
        description="Generate 4 possible subtasks about the question, then propose the solution (with reasoning and calculation). Be detailed: What are the given info, what the step by step solution for each subtask is.",
    )
    statements: List[StatementsPair] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="List of pairs of statements related to the problem. DO NOT GENERATE STATEMENTS NOT VERIFIED BY THE SOLUTION ABOVE.",
    )


def get_images(problem_raw):
    variables = problem_raw["variables"]
    temperature = variables["temperature"]
    time = variables["time"]

    plt.figure(figsize=(8, 5))
    for i in range(len(time) - 1):
        plt.plot([time[i], time[i + 1]], [temperature[i], temperature[i + 1]], "r-")
    plt.scatter(
        time,
        [t if t is not None else np.nan for t in temperature],
        color="b",
        zorder=2,
    )
    plt.xlabel("Thời gian (phút)")
    plt.ylabel("Nhiệt độ (°C)")
    plt.grid(True)

    _, path = mkstemp(suffix=".png")
    plt.savefig(path, format="png")
    return [path]


def handler(prompt_content: str, n_problems: int):
    """
    Takes in content of a prompt and the number of problems to be generated.
    Return problems structured in JSON format.
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

        answer = "".join(np.random.choice(["D", "S"], size=4))
        statements = []
        for j, statement_pair in enumerate(problem_raw["statements"]):
            statement = statement_pair["true" if answer[j] == "D" else "false"]
            statement_prefix = f"{chr(ord('a') + j)})"
            statements.append(f"{statement_prefix} {statement}")

        problem["question"] = "\n\n".join([problem_raw["question"]] + statements)
        problem["solution"] = problem_raw["solution"]
        problem["answers"] = [("*", answer)]
        problem["medias"] = get_images(problem_raw)

    return (problems, response)
