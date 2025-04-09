# Exam Generator Tool

> [!WARNING]
> Still in beta. Breaking changes are expected without notice. Please read
> the documentation carefully.

Exam Generator is a python tool for generating exam.

This tool uses API from [OpenRouter](https://openrouter.ai/).

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
$ python main.py --help

Usage: main.py [OPTIONS]

Generate a contest from prompts.

Options:
  -c, --config=STR         Path to config file. (default: config.toml)
  -o, --output=STR         Path to output. Will be created if not exists. (default: dist/{datetime})
  -r, --raw-content-only   docx and QTI zip files will not be generated.
  -a, --always-use-llm     Always use LLM to generate content instead of asking each time.

Other actions:
  -h, --help               Show the help
```

### Config file

The default config file is at `config.toml`.

```toml
# config.toml

[global]
shuffle = false
back_handler = "default"

[[batch]]
prompt = "informatics/database"
n_problems = 24
front_handler = "multiple_choice/default"

[[batch]]
prompt = "informatics/database"
n_problems = 4
front_handler = "true_false/default"
```

This config file specifies 2 batches. The first one contains 24 problems, using
front handler `multiple_choice/default`. The second one contains 4 problems,
using front handler `true_false/default`. Note how both uses the prompt
`informatics/database`.

Explanation:

- `front_handler = "multiple_choice/default"`:

    - [`handlers/frontHandlers/multiple_choice/default.py`](handlers/frontHandlers/multiple_choice/default.py)
      must contain the function `handler(prompt_content, n_problems)`.

    - `prompt_content` is the prompt to be sent to the LLM.

    - `n_problems` is the number of problems to be generated.

    - The function returns a `dict` (to be written to and read from JSON files).

- `back_handler = "default"`

    - [`handlers/backHandlers/default.py`](handlers/backHandlers/default.py)
      must contain the function `handler(content_dict, path)`.

    - `content_dict` is a dict that maps `batch_{id}` to the LLM's response
      (given by `front_handler`) for that batch.

    - `path` is the output path. Useful if you want to generate images to be
      attached.

    - The function returns a `str` (to be written to the txt content file).

- `prompt = "informatics/database"`:

    - Specifies the prompt at
      [`prompts/informatics/database.txt`](handlers/frontHandlers/multiple_choice/default.py).

- `n_problems = 4`:

    - Specifies the number of problems this batch should generate, in this
      case 4.

    - Sometimes the expected output length may exceed the LLM's limit. In this
      case, you can specify multiple batches while using the same `prompt` and
      `front_handler`.

- `shuffle = false`:

    - Generated problems will not be shuffled. Useful when there are multiple
      batches.

### Output

The default output path is `dist/{datetime}`. The directory structure is as
follows.

```
dist
├── {datetime}:
│     ├── assets
│     │     └── ... # Images to be attached if needed.
│     ├── logs
│     │     └── ... # LLM outputs in JSON format.
│     ├── prompts
│     │     └── ... # Copies of the prompts used.
│     ├── content.txt # Contest problems in QTI-compatible txt format.
│     ├── dethi.docx # Contest problems in docx format.
│     └── qti.zip # QTI file for Canvas.
└── ...
```

> [!WARNING]  
> Docx generation is currently NOT supported for true/false questions.

## More information

For more information about the QTI-compatible text format, consult
[the `text2qti` repository](https://github.com/gpoore/text2qti).

