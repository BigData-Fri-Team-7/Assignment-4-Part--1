# backend/main.py

import os
import json
import boto3
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import tempfile
from pdf_extractor import extract_pdf_content
from llm_chat import get_llm_response

# Load environment variables
load_dotenv()

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_MARKDOWN_FOLDER = "Markdowns/"

# Initialize FastAPI
app = FastAPI()

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

########################################
#           Pydantic Models            #
########################################
class MarkdownRequest(BaseModel):
    markdown_filename: str

class ChatRequest(BaseModel):
    question: str
    pdf_json: str | None = None
    markdown_filename: str | None = None
    llm_choice: str

########################################
#         S3 Utility Functions         #
########################################
def get_markdown_from_s3(markdown_filename: str):
    """Fetches the content of a selected Markdown file from S3."""
    object_key = f"{S3_MARKDOWN_FOLDER}{markdown_filename}"
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        markdown_content = response["Body"].read().decode("utf-8")
        return markdown_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Markdown content: {e}")

########################################
#            API Endpoints             #
########################################
@app.get("/fetch_markdown_files/")
def fetch_markdown_files():
    """Fetches Markdown file names from S3."""
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=S3_MARKDOWN_FOLDER)
        files = [obj["Key"].split("/")[-1] for obj in response.get("Contents", [])]
        return {"markdown_files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Markdown files: {e}")

@app.post("/get_markdown_content/")
def get_markdown_content(request: MarkdownRequest):
    """Fetches the content of a selected Markdown file from S3."""
    markdown_content = get_markdown_from_s3(request.markdown_filename)
    return {"markdown_content": markdown_content}

"""
@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    
    #Uploads a PDF, extracts its content, and returns structured JSON.
    
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        pdf_data = extract_pdf_content(tmp_path)
        os.remove(tmp_path)  # Clean up temporary file
        return JSONResponse(content=pdf_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
"""
@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Uploads a PDF, extracts its content using pdf_extractor.py, and returns structured JSON.
    """
    try:
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        from pdf_extractor import extract_pdf_content
        pdf_data = extract_pdf_content(tmp_path)
        os.remove(tmp_path)  # Clean up temporary file
        return JSONResponse(content=pdf_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")




@app.post("/convert_pdf_markdown/")
async def convert_pdf_markdown(file: UploadFile = File(...)):
    """
    Uploads a PDF, checks if a Markdown with the same name already exists in S3,
    if not, converts it to Markdown using pdf_markdown_convertor.py logic,
    uploads the Markdown file to S3, and returns the Markdown file URL.
    """
    original_pdf_name = file.filename  # e.g. "MyDocument.pdf"
    markdown_filename = os.path.splitext(original_pdf_name)[0] + ".md"
    object_key = f"{S3_MARKDOWN_FOLDER}{markdown_filename}"

    # 1) Check for a duplicate markdown in S3
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=object_key)
        # If no exception, the file already exists
        raise HTTPException(
            status_code=400,
            detail=f"Markdown '{markdown_filename}' already exists in S3. Duplicate not allowed."
        )
    except s3_client.exceptions.ClientError as e:
        # If it's a 404, that means the object doesn't exist => proceed
        if e.response["Error"]["Code"] != "404":
            raise

    # 2) Convert to Markdown (no duplicate found)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        # Pass original_pdf_name so the converter uses the PDF's base name for .md
        from pdf_markdown_convertor import pdf_to_markdown_s3
        markdown_url = pdf_to_markdown_s3(pdf_path=tmp_path, original_filename=original_pdf_name)
        
        os.remove(tmp_path)
        return JSONResponse(content={"markdown_url": markdown_url})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error converting PDF to Markdown: {str(e)}")

        

@app.post("/chat/")
def chat(request: ChatRequest):
    """
    Handles chat requests using either extracted PDF data or Markdown content.
    """
    try:
        if request.pdf_json:
            pdf_data = json.loads(request.pdf_json)
            answer = get_llm_response(pdf_data, request.question, request.llm_choice)
        elif request.markdown_filename:
            markdown_content = get_markdown_from_s3(request.markdown_filename)
            markdown_data = {"pdf_content": markdown_content, "tables": []}
            answer = get_llm_response(markdown_data, request.question, request.llm_choice)
        else:
            return {"error": "No valid input provided."}
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {e}")

# Add these helper functions in backend/main.py (or a separate module if preferred)

@app.post("/summarize/")
def summarize(request: ChatRequest):
    """
    Handles summarize requests using either extracted PDF data or Markdown content.
    Overrides the user's question with a fixed prompt to summarize the document in 200 words.
    """
    summary_question = "Summarise this in 200 words"
    try:
        if request.pdf_json:
            pdf_data = json.loads(request.pdf_json)
            answer = get_llm_response(pdf_data, summary_question, request.llm_choice)
        elif request.markdown_filename:
            markdown_content = get_markdown_from_s3(request.markdown_filename)
            markdown_data = {"pdf_content": markdown_content, "tables": []}
            answer = get_llm_response(markdown_data, summary_question, request.llm_choice)
        else:
            return {"error": "No valid input provided."}
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing summarize request: {e}")



def convert_table_to_markdown(table):
    """
    Converts a list of dictionaries (one table) to a markdown table.
    Assumes each dict represents a row and uses the keys of the first row as headers.
    """
    if not table:
        return ""
    headers = list(table[0].keys())
    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in table:
        md += "| " + " | ".join(str(row.get(header, "")) for header in headers) + " |\n"
    return md

def convert_tables_to_markdown(tables):
    """
    Converts all extracted tables to markdown format.
    """
    md_tables = ""
    for idx, table in enumerate(tables, start=1):
        md_tables += f"### Table {idx}\n\n"
        md_tables += convert_table_to_markdown(table) + "\n\n"
    return md_tables

def upload_markdown_from_pdf(pdf_filename: str, pdf_data: dict) -> str:
    """
    Generates a markdown file from the PDF data, checks if a markdown file with the same
    name already exists in S3, and if not, uploads it.
    Returns the S3 URL of the markdown file.
    """
    import os
    # Derive the markdown filename from the PDF filename
    markdown_filename = os.path.splitext(pdf_filename)[0] + ".md"
    s3_markdown_key = f"{S3_MARKDOWN_FOLDER}{markdown_filename}"
    
    # Check if the markdown file already exists in S3
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_markdown_key)
        # Markdown exists – build its URL
        markdown_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{s3_markdown_key}"
        return markdown_url
    except s3_client.exceptions.ClientError as e:
        if e.response["Error"]["Code"] != "404":
            raise e  # re-raise if it's not a "not found" error
    
    # Build markdown content
    markdown_content = f"# Extracted Content from {pdf_filename}\n\n"
    markdown_content += pdf_data.get("pdf_content", "") + "\n\n"
    if pdf_data.get("tables"):
        markdown_content += "## Tables Extracted\n\n"
        markdown_content += convert_tables_to_markdown(pdf_data.get("tables"))
    
    # Upload the markdown content to S3
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_markdown_key,
        Body=markdown_content.encode("utf-8"),
        ContentType="text/markdown"
    )
    markdown_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com/{s3_markdown_key}"
    return markdown_url

@app.post("/estimate_cost/")
def estimate_cost(request: ChatRequest):
    """
    Estimates token count and cost for the given prompt.
    """
    import json
    from llm_chat import count_tokens, build_prompt
    # Build the prompt based on input (using either pdf_json or markdown)
    if request.pdf_json:
        pdf_data = json.loads(request.pdf_json)
    elif request.markdown_filename:
        pdf_content = get_markdown_from_s3(request.markdown_filename)
        pdf_data = {"pdf_content": pdf_content, "tables": []}
    else:
        raise HTTPException(status_code=400, detail="No valid input provided.")
    
    prompt_text = build_prompt(pdf_data, request.question)
    token_count = count_tokens(prompt_text, model=request.llm_choice)
    
    # Updated cost per token rates (cost per million tokens divided by 1,000,000)
    cost_rates = {
        "gpt-4o": 0.15 / 1_000_000,            # $0.15 per million tokens
        "gemini flash free": 0.0,
        "deepseek": 0.07 / 1_000_000,            # $0.07 per million tokens
        "claude-3.5 haiku": 0.80 / 1_000_000     # $0.80 per million tokens
    }
    rate = cost_rates.get(request.llm_choice.lower(), 0.01 / 1_000_000)
    estimated_cost = token_count * rate
    
    return {"token_count": token_count, "estimated_cost": estimated_cost}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
