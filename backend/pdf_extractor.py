# backend/pdf_extractor.py

import PyPDF2
import camelot
import json
import re

def clean_text(text):
    """Removes excessive spaces, newlines, and unwanted symbols from extracted text."""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces/newlines with a single space
    text = text.replace("\ufeff", "").strip()  # Remove invisible BOM characters
    return text

def extract_pdf_content(pdf_path: str) -> dict:
    """Extracts text and tables from a PDF and structures it for LLM processing."""
    text_content = ""
    
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n\n"

    # Clean extracted text
    text_content = clean_text(text_content)

    # Extract tables using Camelot
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

if __name__ == "__main__":
    # For testing standalone extraction
    pdf_file = "C:/Users/Administrator/Downloads/Assignment 4-Part 1 Spring 2025.pdf"  # Update the path
    extracted_data = extract_pdf_content(pdf_file)
    output_file = "clean_pdf_content.json"
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(extracted_data, json_file, indent=2)
    print(f"Cleaned extracted content saved to {output_file}")
