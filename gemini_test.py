from google import generativeai as genai
import PyPDF2
import camelot
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace("\ufeff", "").strip()
    return text

def extract_pdf_content(pdf_path: str) -> dict:
    text_content = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n\n"
    text_content = clean_text(text_content)
    tables_data = []
    try:
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
        for table in tables:
            tables_data.append(table.df.to_dict(orient="records"))
    except Exception as e:
        print(f"Error extracting tables: {e}")
    return {
        "pdf_content": text_content,
        "tables": tables_data
    }

def ask_gemini_with_pdf_content(pdf_content: str, question: str) -> str:
    api_key = "AIzaSyDseYE1Io995FEXahokfO8eNnDwVV856ME"  # Replace with your actual API key

    genai.configure(api_key=api_key)

    # **CHANGE THIS LINE:**
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')  # or try 'models/gemini-1.5-pro-002' or 'models/gemini-1.5-pro'

    prompt_content = f"""
    Based on the following document content:

    {pdf_content}

    ---

    Answer this question: {question}
    """

    try:
        # You can add temperature here, if desired:
        response = model.generate_content(prompt_content) # , generation_config=genai.GenerationConfig(temperature=0.7)
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini API: {e}"

if __name__ == "__main__":
    pdf_file = "C:/Users/Administrator/Downloads/Assignment 4-Part 1 Spring 2025.pdf"
    extracted_data = extract_pdf_content(pdf_file)
    pdf_text_content = extracted_data["pdf_content"]

    if pdf_text_content:
        user_question = "What is the main topic of this document?"
        gemini_response = ask_gemini_with_pdf_content(pdf_text_content, user_question)

        print("\n--- Gemini API Response ---")
        print(gemini_response)
    else:
        print("No text content extracted from PDF to send to Gemini API.")