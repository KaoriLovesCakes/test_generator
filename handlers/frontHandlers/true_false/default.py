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
    question: str = Field(
        ...,
        description="The question itself, providing context, numbers, events, etc. MUST INCLUDE THE CONTEXT ABOVE. Be LONG and VERY DETAILED!",
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
    Return LLM's response.
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
            "temperature": 1.2,
        },
    ).text
    assert response_raw is not None

    response = json.loads(response_raw)
    for key in response.keys():
        response[key]["answer"] = "".join(np.random.choice(["D", "S"], size=4))
        response[key]["ptype"] = "true_false"

    return response
