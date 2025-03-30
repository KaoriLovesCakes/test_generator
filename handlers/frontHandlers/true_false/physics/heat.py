import json
import os
from typing import List

import dotenv
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
        description="The question's context.",
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


def handler(prompt_content: str, n_problems: int):
    """
    Takes in content of a prompt and the number of problems to be generated.
    Return the LLM's response in JSON format.
    """

    response_raw = client.models.generate_content(
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
    assert response_raw is not None

    response = json.loads(response_raw)
    for key in response.keys():
        response[key]["is_true"] = np.random.randint(2, size=4).tolist()
        response[key]["ptype"] = "true_false"

    return response
