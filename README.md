# Resume File Assistant

A small Python project demonstrating LLM function calling with local file tools. The assistant can list resume files, extract PDF/TXT/DOCX text, search for keywords, and write a summary file.

## Requirements

- Python 3.10+
- An OpenAI API key

## Setup

Run these commands in the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:OPENAI_API_KEY = "your-api-key"
```

Optionally choose a model with `$env:OPENAI_MODEL = "gpt-4o-mini"`. The default is `gpt-4o-mini`.

## Run the assistant

Pass a request in quotes:

```powershell
python llm_file_assistant.py "Read all resumes in the resumes folder"
python llm_file_assistant.py "Find resumes mentioning Python experience in resumes"
python llm_file_assistant.py "Create a summary file for resumes\resume_john_doe.txt"
```

The model calls tools as needed. The fourth example asks it to read the resume, summarize the content, and write a summary file. Tool paths are local paths interpreted from the current working directory.

## File tools without an LLM

The functions can be imported and used directly:

```python
from fs_tools import list_files, read_file, search_in_file, write_file

files = list_files("resumes", ".txt")
resume = read_file("resumes/resume_john_doe.txt")
matches = search_in_file("resumes/resume_john_doe.txt", "Python")
saved = write_file("output/example.txt", "Example summary")
```

`read_file` returns a dictionary with `success`, extracted `content`, and file `metadata` on success. `search_in_file` returns a match count and context snippets. `list_files` returns metadata records for direct child files (not recursive); invalid directories produce an error record. `write_file` creates missing parent directories and returns a status dictionary. Supported read/search formats are PDF, TXT, and DOCX.

## Sample data

The `resumes` directory includes six fictional TXT resumes. All names, organizations, and contact details are invented for this demonstration.

## Demo video walkthrough (2–3 minutes)

No screen-recording utility is available in this project environment, so an actual video file is not included. Use this walkthrough to record the required demo:

1. Show the project files and the six sample resumes.
2. Set `OPENAI_API_KEY` and run `python llm_file_assistant.py "Read all resumes in the resumes folder"`.
3. Run `python llm_file_assistant.py "Find resumes mentioning Python experience in resumes"` and show the names and matching experience.
4. Run `python llm_file_assistant.py "Create a summary file for resumes\resume_john_doe.txt"` and show the generated summary file.
5. Briefly show `fs_tools.py` and explain that the LLM selects the tools and the Python functions perform the file operations.

## Notes

- Text extraction from scanned/image-only PDFs depends on OCR, which this project does not include.
- The LLM call requires network access and incurs API usage according to the selected OpenAI model.
- Review generated summaries before using them; the model may omit or misinterpret details.
