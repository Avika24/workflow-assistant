import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import pdfplumber


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


genai.configure(api_key=api_key, transport='rest')


model = genai.GenerativeModel("gemini-2.5-flash")


st.set_page_config(page_title="Mini Workflow Assistant", page_icon="🤖")
st.title("🤖 Mini Workflow Assistant")
st.write("Upload a PDF/TXT or paste notes to get a summary + action items.")


uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
manual_text = st.text_area("Or paste your notes here", height=200)

text = ""


if uploaded_file:
    if uploaded_file.type == "application/pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            # Extract text from every page and join it
            content = [page.extract_text() for page in pdf.pages if page.extract_text()]
            text = "\n".join(content)
    else:
        text = uploaded_file.read().decode("utf-8")


if manual_text.strip():
    text = manual_text


if st.button("Generate Insights"):
    if not text.strip():
        st.error("Please upload a file or paste text first.")
    else:
        
        prompt = f"""
        Act as a professional assistant. Review the following notes and provide:
        1. A brief summary of the main context.
        2. Key takeaways in a bulleted list.
        3. A structured To-Do list for the user.
        4. Any specific deadlines, dates, or contact info mentioned.

        Notes:
        {text}
        """

        with st.spinner("Processing your workflow..."):
            try:
                response = model.generate_content(prompt)
                st.subheader("📋 Results")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error: {e}")
        