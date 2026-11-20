# DocFlow — AI Document Workflow Assistant

DocFlow turns pasted text, TXT files, and text-based PDFs into a structured summary, action items, and key dates. Every action item includes a source quote and a verification status.

## Features

- Gemini-powered summaries, key points, action items, owners, deadlines, and key dates.
- Pydantic validation with one retry for malformed responses.
- Evidence quote verification using normalized matching and a fuzzy similarity fallback.
- Pasted text, TXT, and text-based PDF inputs.
- Relative date resolution against a selected document date.
- Summary, Action Items, and Key Dates tabs with CSV and JSON downloads.
- Friendly errors for missing configuration, empty/scanned PDFs, invalid input, and API failures.
- Automated tests with Gemini mocked; tests do not consume API quota.

## Architecture

~~~mermaid
flowchart TD
 A[Paste text / TXT / PDF] --> B[loaders.py]
 B --> C[Clean document text]
 C --> D[extractor.py]
 D --> E[Gemini API]
 E --> F[Pydantic validation]
 F -->|Invalid JSON/schema| G[One retry]
 G --> E
 F --> H[verify.py]
 H --> I[Evidence quote check]
 I --> J[app.py — Streamlit]
 J --> K[Summary]
 J --> L[Action Items]
 J --> M[Key Dates]
 J --> N[CSV / JSON export]
~~~

## Tech stack

Python, Streamlit, Google Gemini API (the supported `google-genai` SDK), Pydantic, pypdf, pandas, python-dotenv, and Pytest.

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/Avika24/workflow-assistant.git
   cd workflow-assistant
   ```

2. Create and activate a virtual environment.

   **Windows PowerShell**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS / Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and add your Gemini API key to `GEMINI_API_KEY`. Keep `.env` private. The model defaults to `gemini-3.8-flash`; set `GEMINI_MODEL` to override it.

5. Run the application:

   ```bash
   streamlit run app.py
   ```


## Deploy on Streamlit Community Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Select **Create app** and choose repository `Avika24/workflow-assistant`, branch `main`, and main file path `app.py`.
3. In **Advanced settings**, select Python 3.12.
4. In the **Secrets** field, add the following TOML (replace the placeholder with your own key):

   ```toml
   GEMINI_API_KEY = "your_gemini_api_key"
   GEMINI_MODEL = "gemini-3.8-flash"
   ```

5. Click **Deploy**. Keep the key in Streamlit Secrets; never commit it to GitHub.

See the [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app) for current instructions.

## Project structure

```text
workflow-assistant/
├── app.py
├── extractor.py
├── loaders.py
├── schemas.py
├── verify.py
├── tests/
│   ├── test_extractor.py
│   ├── test_loaders.py
│   ├── test_schemas.py
│   └── test_verify.py
├── samples/
│   ├── meeting_notes.txt
│   ├── project_brief.txt
│   └── team_updates.txt
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Tests

Run `pytest -v`. Gemini is mocked in tests, so the suite does not require an API key or network access.

## Example

See `samples/meeting_notes.txt`. It includes explicit owners, relative deadlines, and key dates. Review actual extracted output because LLM date interpretation and task assignment can still be imperfect.

## Screenshots

### Input screen
<img width="1920" height="1020" alt="Screenshot 2026-11-20 233016" src="https://github.com/user-attachments/assets/99baedf0-fc0f-4c20-99a0-258fa9cc4df8" />


### Extracted results
<img width="1920" height="1020" alt="Screenshot 2026-11-20 233112" src="https://github.com/user-attachments/assets/a7fbf63b-86d9-4759-bf75-b1b1833cf7ef" />


## Limitations

- Scanned PDFs are unsupported; OCR is intentionally out of scope.
- A quote-presence check does not prove that the task interpretation is correct or eliminate hallucinations.
- The LLM can miss or misassign action items.
- The project has not been evaluated on a large dataset.
- Current prompting and interface are English-only.

## Future improvements

- Optional calendar export (`.ics`).
- A manually reviewed evaluation set using more varied documents.
- Optional hosted demo using platform secrets for the API key.
