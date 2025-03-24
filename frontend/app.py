import streamlit as st
import requests
import json
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_MARKDOWN_FOLDER = "Markdowns/"

# Backend Endpoints
UPLOAD_URL = "https://assignment-4-part-1.onrender.com/upload_pdf/"
CONVERT_PDF_MARKDOWN_URL = "https://assignment-4-part-1.onrender.com/convert_pdf_markdown/"
CHAT_URL = "https://assignment-4-part-1.onrender.com/chat/"
ESTIMATE_COST_URL = "https://assignment-4-part-1.onrender.com/estimate_cost/"  # new endpoint for cost estimation
FETCH_MARKDOWN_URL = "https://assignment-4-part-1.onrender.com/fetch_markdown_files/"
GET_MARKDOWN_CONTENT_URL = "https://assignment-4-part-1.onrender.com/get_markdown_content/"
SUMMARIZE_URL = "https://assignment-4-part-1.onrender.com/summarize/"

# Initialize S3 Client (if needed)
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

# Use session state to avoid re-running PDF extraction on every UI interaction
if "pdf_data" not in st.session_state:
    st.session_state.pdf_data = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = None

st.title("📄 PDF & Markdown Chatbot with LLM")

# Three modes: Upload PDF for chat, Use Existing Markdown, or Convert PDF to Markdown
input_method = st.radio(
    "Select Input Method",
    ("Upload PDF", "Use Existing Markdown", "Convert PDF to Markdown")
)

# ------------------- Mode 1: Upload PDF (for Chat) --------------------- #
if input_method == "Upload PDF":
    st.header("Upload a PDF for Chat")
    if st.session_state.pdf_data:
        st.info(f"PDF '{st.session_state.pdf_filename}' is already loaded. You can ask questions below!")
        if st.button("Clear Loaded PDF", key="clear_pdf"):
            st.session_state.pdf_data = None
            st.session_state.pdf_filename = None
            st.experimental_rerun()
    else:
        uploaded_file = st.file_uploader("📂 Choose a PDF file", type=["pdf"], key="upload_pdf")
        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            with st.spinner("⏳ Extracting PDF content..."):
                files = {"file": (uploaded_file.name, file_bytes, "application/pdf")}
                response = requests.post(UPLOAD_URL, files=files)
                if response.status_code == 200:
                    st.session_state.pdf_data = response.json()
                    st.session_state.pdf_filename = uploaded_file.name
                    st.success(f"✅ PDF content extracted successfully for '{uploaded_file.name}'!")
                else:
                    st.error("❌ Failed to extract PDF content")
                    st.session_state.pdf_data = None

# ------------------- Mode 2: Use Existing Markdown ---------------------- #
elif input_method == "Use Existing Markdown":
    st.header("Use a Markdown File from S3")
    def fetch_markdown_files():
        """Fetch Markdown files stored in S3."""
        response = requests.get(FETCH_MARKDOWN_URL)
        if response.status_code == 200:
            return response.json().get("markdown_files", [])
        return []
    markdown_files = fetch_markdown_files()
    if markdown_files:
        selected_md = st.selectbox("📜 Select a Markdown file:", markdown_files, key="markdown_select")
        if st.button("🔍 View Markdown Content", key="view_markdown"):
            if selected_md:
                response = requests.post(
                    GET_MARKDOWN_CONTENT_URL,
                    json={"markdown_filename": selected_md}
                )
                if response.status_code == 200:
                    markdown_text = response.json().get("markdown_content", "")
                    st.text_area("📄 Markdown Content", markdown_text, height=300, key="markdown_text")
                else:
                    st.error(f"❌ Failed to retrieve Markdown content: {response.text}")
            else:
                st.warning("⚠️ Please select a Markdown file.")
    else:
        st.warning("⚠️ No Markdown files found in S3.")

# ------------------- Mode 3: Convert PDF to Markdown -------------------- #
elif input_method == "Convert PDF to Markdown":
    st.header("Convert PDF to Markdown & Upload to S3")
    uploaded_pdf = st.file_uploader("Select a PDF to convert", type=["pdf"], key="convert_pdf")
    if uploaded_pdf is not None:
        with st.spinner("⏳ Checking & Converting..."):
            file_bytes = uploaded_pdf.getvalue()
            files = {"file": (uploaded_pdf.name, file_bytes, "application/pdf")}
            resp = requests.post(CONVERT_PDF_MARKDOWN_URL, files=files)
            if resp.status_code == 200:
                data = resp.json()
                st.success("✅ PDF converted to Markdown and uploaded to S3!")
                st.write("**Markdown URL:**", data.get("markdown_url"))
            else:
                st.error(f"❌ Could not convert PDF. {resp.text}")

# --------------------- LLM Chat Section ---------------------------- #
# Only display chat if user selected "Upload PDF" or "Use Existing Markdown"
if input_method in ("Upload PDF", "Use Existing Markdown"):
    st.header("💬 Ask a Question")
    llm_option = st.selectbox("🤖 Select LLM", ["gpt-4o", "Gemini Flash Free", "DeepSeek", "Claude-3.5 Haiku"], key="llm_option")
    user_question = st.text_input("📝 Your question:", key="user_question")
    
    # Add a new button to estimate token count and cost
    if st.button("💰 Estimate Tokens & Cost", key="estimate_cost"):
        # Build the data to send for estimation (similar to chat request)
        if input_method == "Upload PDF":
            if st.session_state.pdf_data:
                data = {
                    "question": user_question,
                    "pdf_json": json.dumps(st.session_state.pdf_data),
                    "llm_choice": llm_option
                }
            else:
                st.warning("⚠️ Please upload a PDF first.")
                data = None
        elif input_method == "Use Existing Markdown":
            if "selected_md" in locals() and selected_md:
                data = {
                    "question": user_question,
                    "markdown_filename": selected_md,
                    "llm_choice": llm_option
                }
            else:
                st.warning("⚠️ Please select a Markdown file.")
                data = None
        else:
            data = None

        if data:
            with st.spinner("⏳ Estimating..."):
                est_resp = requests.post(ESTIMATE_COST_URL, json=data)
                if est_resp.status_code == 200:
                    est_data = est_resp.json()
                    token_count = est_data.get("token_count", 0)
                    estimated_cost = est_data.get("estimated_cost", 0.0)
                    st.success("✅ Estimation complete!")
                    st.write(f"**Token Count:** {token_count}")
                    st.write(f"**Estimated Cost:** ${estimated_cost:.4f}")
                else:
                    st.error("❌ Failed to estimate cost: " + est_resp.text)
    
    # Button to send question
    if st.button("🚀 Send Question", key="send_question"):
        if input_method == "Upload PDF":
            if st.session_state.pdf_data:
                data = {
                    "question": user_question,
                    "pdf_json": json.dumps(st.session_state.pdf_data),
                    "llm_choice": llm_option
                }
            else:
                st.warning("⚠️ Please upload a PDF first.")
                data = None
        elif input_method == "Use Existing Markdown":
            if "selected_md" in locals() and selected_md:
                data = {
                    "question": user_question,
                    "markdown_filename": selected_md,
                    "llm_choice": llm_option
                }
            else:
                st.warning("⚠️ Please select a Markdown file.")
                data = None
        else:
            st.warning("⚠️ Please use 'Upload PDF' or 'Use Existing Markdown' to chat.")
            data = None

        if data:
            with st.spinner("⏳ Generating answer..."):
                response = requests.post(CHAT_URL, json=data)
                if response.status_code == 200:
                    answer = response.json().get("answer", "No answer received.")
                    st.write("💡 **Answer:**", answer)
                else:
                    st.error("❌ Error from backend: " + response.text)
    
    # ----------------- New Summarize Button ----------------- #
    if st.button("📝 Summarize", key="summarize_button"):
        summary_question = "Summarise this in 200 words"
        if input_method == "Upload PDF":
            if st.session_state.pdf_data:
                data = {
                    "question": summary_question,
                    "pdf_json": json.dumps(st.session_state.pdf_data),
                    "llm_choice": llm_option
                }
            else:
                st.warning("⚠️ Please upload a PDF first.")
                data = None
        elif input_method == "Use Existing Markdown":
            if "selected_md" in locals() and selected_md:
                data = {
                    "question": summary_question,
                    "markdown_filename": selected_md,
                    "llm_choice": llm_option
                }
            else:
                st.warning("⚠️ Please select a Markdown file.")
                data = None
        else:
            data = None

        if data:
            with st.spinner("⏳ Generating summary..."):
                response = requests.post(SUMMARIZE_URL, json=data)
                if response.status_code == 200:
                    summary = response.json().get("answer", "No summary received.")
                    st.write("💡 **Summary:**", summary)
                else:
                    st.error("❌ Error from backend: " + response.text)
