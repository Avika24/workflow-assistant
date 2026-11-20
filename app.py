"""DocFlow — AI Document Workflow Assistant."""
from datetime import date
import json
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from extractor import ExtractionError, analysis_to_dict, extract_analysis
from loaders import DocumentLoadError, load_uploaded_file
from verify import verify_action_items

load_dotenv()


def _load_streamlit_secrets() -> None:
    """Expose Streamlit Cloud secrets through the same config used locally."""
    try:
        for key in ("GEMINI_API_KEY", "GEMINI_MODEL"):
            if not os.getenv(key) and key in st.secrets:
                os.environ[key] = str(st.secrets[key])
    except FileNotFoundError:
        # Local development normally uses .env and has no Streamlit secrets.toml.
        pass


_load_streamlit_secrets()
st.set_page_config(page_title="DocFlow", page_icon="📄", layout="wide")

st.title("📄 DocFlow")
st.caption("AI document workflow assistant · Summaries, action items, and key dates with source evidence")

st.sidebar.header("Document settings")
document_date = st.sidebar.date_input("Document date", value=date.today())
st.sidebar.caption("Relative dates are resolved against this date.")

uploaded = st.file_uploader("Upload a text-based PDF or TXT file", type=["pdf", "txt"])
manual_text = st.text_area(
    "Or paste your document text",
    height=220,
    placeholder="Paste meeting notes, project briefs, or team updates...",
)

source_text = ""
source_name = "Pasted text"
if manual_text.strip():
    source_text = manual_text.strip()
elif uploaded is not None:
    try:
        source_text = load_uploaded_file(uploaded.name, uploaded.getvalue())
        source_name = uploaded.name
        st.success(f"Loaded {uploaded.name}")
    except DocumentLoadError as exc:
        st.error(str(exc))

if st.button("Analyze document", type="primary", width="stretch"):
    if not source_text:
        st.error("Add document text or upload a valid TXT/PDF file before analyzing.")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("Gemini API key is missing. Add GEMINI_API_KEY to your .env file and restart DocFlow.")
    else:
        with st.spinner("Reading document and validating extracted information..."):
            try:
                result = extract_analysis(source_text, document_date)
                result_dict = analysis_to_dict(result)
                checks = verify_action_items(source_text, result.action_items)
                for item, check in zip(result_dict["action_items"], checks):
                    item["evidence_verified"] = check["verified"]
                    item["evidence_similarity"] = check["similarity"]
                    item["evidence_warning"] = check["warning"]
                st.session_state["docflow_result"] = result_dict
                st.session_state["docflow_source_name"] = source_name
            except ExtractionError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unexpected error while analyzing the document: {exc}")

result = st.session_state.get("docflow_result")
if result:
    items = result.get("action_items", [])
    flagged = sum(not item.get("evidence_verified", False) for item in items)

    metric_cols = st.columns(3)
    metric_cols[0].metric("Action items", len(items))
    metric_cols[1].metric("Key dates", len(result.get("key_dates", [])))
    metric_cols[2].metric("Evidence flags", flagged)
    if flagged:
        st.warning(f"{flagged} action item(s) have evidence quotes that could not be verified in the source.")

    summary_tab, action_tab, dates_tab = st.tabs(["Summary", "Action Items", "Key Dates"])
    with summary_tab:
        st.subheader("Document summary")
        st.write(result["summary"])
        st.subheader("Key points")
        for point in result.get("key_points", []):
            st.markdown(f"- {point}")
        st.caption(f"Source: {st.session_state.get('docflow_source_name', 'Document')}")

    with action_tab:
        st.subheader("Action items")
        if items:
            rows = [
                {
                    "Task": item["task"],
                    "Owner": item.get("owner") or "Not stated",
                    "Deadline": item.get("deadline") or "Not stated",
                    "Priority": item["priority"].title(),
                    "Evidence status": "Verified" if item.get("evidence_verified") else "⚠ Not found in source",
                    "Evidence quote": item["evidence"],
                }
                for item in items
            ]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            for index, item in enumerate(items, start=1):
                with st.expander(f"Action {index}: {item['task']}"):
                    st.write(f"**Evidence:** “{item['evidence']}”")
                    if item.get("evidence_verified"):
                        st.success(f"Evidence found (similarity {item.get('evidence_similarity', 1.0):.3f}).")
                    else:
                        st.warning("⚠ not found in source")
        else:
            st.info("No action items were identified.")

    with dates_tab:
        st.subheader("Key dates")
        key_dates = result.get("key_dates", [])
        if key_dates:
            dates_frame = pd.DataFrame(key_dates).rename(columns={"event": "Event", "date": "Date"})
            st.dataframe(dates_frame, width="stretch", hide_index=True)
        else:
            st.info("No key dates were identified.")

    csv_rows = [
        {
            "task": item["task"],
            "owner": item.get("owner"),
            "deadline": item.get("deadline"),
            "priority": item["priority"],
            "evidence": item["evidence"],
            "evidence_verified": item.get("evidence_verified", False),
        }
        for item in items
    ]
    csv_col, json_col = st.columns(2)
    with csv_col:
        st.download_button(
            "Download action items (CSV)",
            pd.DataFrame(csv_rows).to_csv(index=False),
            "docflow_action_items.csv",
            "text/csv",
            width="stretch",
        )
    with json_col:
        st.download_button(
            "Download full analysis (JSON)",
            json.dumps(result, indent=2, ensure_ascii=False),
            "docflow_analysis.json",
            "application/json",
            width="stretch",
        )
else:
    st.info("Your analysis will appear here after you click **Analyze document**.")
