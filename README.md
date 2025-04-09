# Exam Generator Tool

> [!WARNING] Still in beta. Breaking changes are expected without notice. Please
> read the documentation carefully.

Exam Generator is a Python tool for generating exam.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [More information](#more-information)

## Installation

### Python

Python 3.9+ is tested and officially supported.

Install dependencies with the following commands.

- For Unix systems:

    ```bash
    python -m venv venv
    source ./venv/bin/activate
    pip install -r requirements.txt
    ```

    [devenv](https://devenv.sh/) users can simply clone this repository then run
    `devenv shell` to drop into a virtual environment with the necessary
    dependencies.

- For Windows Powershell:

    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

### API key

Create a file `.env` at the root of the project and set the following variables.
`API_KEY` is required, `MODEL` is optional.

```env
API_KEY=<YOUR_API_KEY>
MODEL=<MODEL>
```

If you are using the officially supported handlers, please use your Google AI
Studio API. The following models have been tested:

- `gemini-2.0-flash` (default)

## Usage

For basic usage, customise `config.toml` to your own liking and simply run
`python main.py`.

Find all options by running `python main.py --help`.

```
Usage: main.py [OPTIONS]

Generate a exam from LLM prompts.

Options:
  -c, --config=STR         Path to config file. (default: config.toml)
  -o, --output=STR         Path to output. Will be created if not exists. (default: dist/{datetime})
  -r, --raw-content-only   docx and QTI zip files will not be generated.

Other actions:
  -h, --help               Show the help
  --txt-to-docx            Generate exam content in docx format from QTI-compatible text format.
  --txt-to-docx-qti        Generate exam content in docx format, along with exam in QTI format, from QTI-compatible text format.
  --txt-to-qti             Generate exam in QTI format from QTI-compatible text format.
```

### Config file

The default config file is at `config.toml`.

```toml
# config.toml

[global]
shuffle = false

[[batch]]
prompt = "informatics/database.txt"
n_problems = 24
handler = "multiple_choice/default"

[[batch]]
prompt = "informatics/database.txt"
n_problems = 4
handler = "true_false/default"
```

This config file specifies 2 batches. The first one contains 24 problems, using
handler `multiple_choice/default`. The second one contains 4 problems, using
handler `true_false/default`. Note how both uses the prompt
`informatics/database.txt`.

Explanation:

- `shuffle = false`:

    - Generated problems will not be shuffled. Set `shuffle = true` if needed
      when there are multiple batches.

- `prompt = "informatics/database"`:

    - Specifies the prompt at
      [`prompts/informatics/database.txt`](handlers/frontHandlers/multiple_choice/default.py).

- `n_problems = 4`:

    - Specifies the number of problems this batch should generate, in this
      case 4.

    - Sometimes the expected output length may exceed the LLM's limit. In this
      case, you can specify multiple batches while using the same `prompt` and
      `handler`.

- `handler = "multiple_choice/default"`:

    - [`handlers/custom/multiple_choice/default.py`](handlers/frontHandlers/multiple_choice/default.py)
      must contain the function `handler(prompt_content, n_problems)`.

    - `prompt_content`: the prompt to be sent to the LLM.

    - `n_problems`: the number of problems to be generated.

    - The function returns a tuple `(problems, response)`.

        - `problems` is a dict with the following keys:

            - `question`: a string, containing the question text

            - `solution`: a string, containing the solution text

            - `answers`: a list of tuples of two strings (the answer prefix and
              its content), e.g.

                - `("a)", "...")`: Incorrect choice a) of multiple choice
                  problem.
                - `("b)", "...")`: Correct choice b) of multiple choice problem.
                - `("*", "...")`: Fixed correct answer of fill-in-the-blank
                  problem.

            - `medias`: a list of strings, each containing path to a media to be
              attached to the question text (e.g. image, audio)

Importing medias from URL is currently not supported.

For each batch, instead of generating problems using LLM, you can prepare a
content file in QTI-compatible text format yourself and specify its path using
the key `source`.

```toml
# config_example.toml

[global]
shuffle = false

[[batch]]
source = "examples/example.txt"
```

### Output

The default output path is `dist/{datetime}`. The directory structure is as
follows.

```
dist
├── {datetime}:
│     ├── assets
│     │     └── ... # Images to be attached if needed.
│     ├── prompts
│     │     └── ... # Copies of the prompts used.
│     ├── responses
│     │     └── ... # For each batch, LLM responses in JSON format and problems in QTI-compatible text format.
│     ├── content.txt # Exam problems in QTI-compatible text format.
│     ├── exam.docx # Exam problems in docx format.
│     └── qti.zip # QTI file for Canvas.
└── ...
```

## More information

For more information about the QTI-compatible text format, consult
[the `text2qti` repository](https://github.com/gpoore/text2qti).

Certain image and audio formats are supported, including but not limited to
`png` and `mp3`.
