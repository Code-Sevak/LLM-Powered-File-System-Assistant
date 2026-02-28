
# LLM-Powered-File-System-Assistant

Small utilities to read/search resume files (PDF, DOCX, TXT) and a tiny LLM-integrated assistant that calls those tools.

What is included

- `fs_tools.py` — Core file-system helpers: `read_file`, `list_files`, `write_file`, `search_in_file`.
- `llm_file_assistant.py` — Lightweight assistant that parses simple natural-language queries and invokes the tools. It can use OpenAI for better summaries when `OPENAI_API_KEY` is configured.
- `requirements.txt` — Optional dependencies: `PyPDF2`, `python-docx`, `openai`.

Sample data

During development a small `resumes/` folder was added with example text resumes:

- `resumes/resume_john_doe.txt`
- `resumes/resume_jane_doe.txt`

Running the assistant will also produce summary files in the same folder (for example `resumes/summary_resume_john_doe.txt`).

Installation (recommended)

Use the workspace Python and a virtual environment to avoid polluting your system packages.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you prefer a single command without a venv:

```bash
python3 -m pip install -r requirements.txt
```

Note: when calling `pip` from zsh make sure you don't split the command across lines. Use quotes for versioned package specs if installing manually, for example:

```bash
python3 -m pip install "PyPDF2>=3.0.0" "python-docx>=0.8.11" "openai>=0.27.0"
```

Usage examples (run from repository root)

- List files in the `resumes/` folder:

```bash
python -c "from fs_tools import list_files; import json; print(json.dumps(list_files('resumes'), indent=2))"
```

- Read a specific resume (works for .txt without extra deps):

```bash
python -c "from fs_tools import read_file; import json; print(json.dumps(read_file('resumes/resume_john_doe.txt'), indent=2))"
```

- Ask the assistant to find resumes mentioning a skill:

```bash
python llm_file_assistant.py "Find resumes mentioning Python"
```

- Read all resumes in the `resumes` folder (returns contents + metadata):

```bash
python llm_file_assistant.py "Read all resumes in the resumes folder"
```

- Create a summary file for a specific resume (will write `resumes/summary_<name>.txt`):

```bash
python llm_file_assistant.py "Create a summary file for resume_john_doe.txt"
```

OpenAI / LLM notes

The project includes a simple hook to OpenAI's API for summarization. To enable it, set your API key in the environment and optionally choose a model:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-3.5-turbo"  # optional
python llm_file_assistant.py "Create a summary file for resume_john_doe.txt" --use-llm
```

If the OpenAI package or API key is not present, the assistant falls back to a deterministic heuristic summarizer so basic functionality still works offline.

Troubleshooting

- If PDF or DOCX reading fails, confirm `PyPDF2` and `python-docx` are installed (see `requirements.txt`).
- On macOS with zsh, avoid splitting pip commands across lines; use the `python3 -m pip` form above.

Next steps you might want

- Add unit tests for `fs_tools.py` and `llm_file_assistant.py` (I can add a pytest suite).
- Add richer natural-language parsing or OpenAI function-calling to let an LLM decide which tool to run.
- Add binary resume samples (PDF/DOCX) and enable parsing by installing the dependencies.

If you'd like, I can add tests and run them now, or install the dependencies in your environment and parse a sample PDF/DOCX — tell me which and I'll proceed.

