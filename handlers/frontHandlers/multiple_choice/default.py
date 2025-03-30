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
MODEL = os.environ.get("MODEL") or "gemini-2.0-pro-exp-02-05"

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
        response_curr = response[key]
        ptype = "multiple_choice"
        choices = deepcopy(response_curr["choices_false"])
        answer = np.random.randint(N_CHOICES)
        choices.insert(answer, response_curr["choice_true"])
        loc = locals()
        response_curr.update(
            {_key: loc[_key] for _key in ["choices", "answer", "ptype"]}
        )

    return response
