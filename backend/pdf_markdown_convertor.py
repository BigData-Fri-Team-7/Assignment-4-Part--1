#backend/pdf_markdown_convertor.py

import fitz  # PyMuPDF for image extraction
import pdfplumber  # For text and table extraction
import os
import re
import pandas as pd
import boto3
import tempfile

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_MARKDOWN_FOLDER = "Markdowns/"
# S3 Folders
S3_MARKDOWN_FOLDER = "Markdowns/"
S3_IMAGES_FOLDER = "Images/"

# Manually specify the input PDF path
PDF_PATH = "C:/Users/Administrator/Downloads/VAEs - Week 8.pdf"  #  Change this to your PDF file path

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)


def upload_file_to_s3(file_path, s3_key):
    """Uploads a file to S3 and returns its public URL."""
    try:
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{s3_key}"
        return s3_url
    except Exception as e:
        print(f" Failed to upload {file_path} to S3: {e}")
        return None


def clean_text(text):
    """Removes excessive spaces and unwanted symbols from extracted text."""
    text = re.sub(r"\s+", " ", text)  # Replace multiple spaces/newlines with a single space
    return text.strip()


def extract_pdf_content(pdf_path, s3_image_folder):
    """Extracts text, tables, and images while maintaining document structure."""
    doc = fitz.open(pdf_path)
    md_content = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(len(doc)):
            page = doc[page_num]
            pdf_page = pdf.pages[page_num] if page_num < len(pdf.pages) else None

            # Extract text first
            if pdf_page:
                page_text = pdf_page.extract_text()
                if page_text:
                    md_content += f"{clean_text(page_text)}\n\n"

            # Extract tables
            if pdf_page:
                tables = pdf_page.extract_tables()
                for table in tables:
                    if table:
                        df = pd.DataFrame(table)
                        md_content += f"{df.to_markdown(index=False)}\n\n"

            # Extract images
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                if not base_image:
                    continue

                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                img_filename = f"image_{page_num+1}_{img_index+1}.{image_ext}"

                # Save image temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{image_ext}") as tmp_img:
                    tmp_img.write(image_bytes)
                    tmp_path = tmp_img.name

                # Upload to S3
                s3_url = upload_file_to_s3(tmp_path, f"{s3_image_folder}/{img_filename}")
                os.remove(tmp_path)

                if s3_url:
                    md_content += f"![Image]({s3_url})\n\n"

    doc.close()
    return md_content


def pdf_to_markdown_s3(pdf_path, original_filename=None):
    """
    Extracts PDF content, uploads images, and saves Markdown to S3.
    If original_filename is provided, use that name for the .md file.
    """
    # Derive the base name from either original_filename or pdf_path
    if original_filename:
        pdf_name = os.path.splitext(os.path.basename(original_filename))[0]
    else:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    markdown_filename = f"{pdf_name}.md"

    s3_image_folder = f"{S3_IMAGES_FOLDER}{pdf_name}"
    s3_markdown_key = f"{S3_MARKDOWN_FOLDER}{markdown_filename}"

    md_content = f"# Extracted Content from {pdf_name}\n\n"
    md_content += extract_pdf_content(pdf_path, s3_image_folder)

    # Save Markdown to a temporary file
    markdown_temp_path = os.path.join(tempfile.gettempdir(), markdown_filename)
    with open(markdown_temp_path, "w", encoding="utf-8") as md_file:
        md_file.write(md_content)

    # Upload to S3
    md_s3_url = upload_file_to_s3(markdown_temp_path, s3_markdown_key)
    os.remove(markdown_temp_path)
    print(f"Markdown uploaded to: {md_s3_url}")
    return md_s3_url



# Run the script
if __name__ == "__main__":
    markdown_url = pdf_to_markdown_s3(PDF_PATH)
    print(f"Markdown File URL: {markdown_url}")
