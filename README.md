# Assignment 4 Part 1 – Streamlit & FastAPI LLM Integration


## Project Overview

This project enhances the functionality of Assignment 1 by introducing:
- A **Streamlit** frontend for uploading or selecting PDF files.
- A **FastAPI** backend that processes the PDF content, handles summarization, and answers questions using various Large Language Models (LLMs) via **LiteLLM**.
- A demonstration of token pricing, error handling, and logging for LLM interactions.

---
## 🔗 Live Deployments

- **Frontend (Streamlit)** → https://assignment-4-part--1.streamlit.app/
- **Backend (FastAPI)** → https://assignment-4-part-1.onrender.com

 #Code lab: https://codelabs-preview.appspot.com/?file_id=17i-15Q0AgWcH9vOmXQGUQJjV4O1AeEa3Z4hQjMt81C0#0
---

## Features

1. **PDF Upload**  
   - Upload a new PDF or select from previously parsed PDFs.

2. **LLM Selection**  
   - Choose from multiple LLMs (e.g., GPT-4o, Gemini Flash, Claude, Grok, DeepSeek).

3. **Summarization**  
   - Generate concise summaries of uploaded/selected PDFs.

4. **Question & Answer**  
   - Ask questions about the PDF content and receive answers in real-time.

5. **User-Friendly Interface**  
   - **Streamlit** provides an intuitive UI for all interactions.

---

## Tech Stack

| Layer        | Technology         | Purpose                                           |
|--------------|--------------------|---------------------------------------------------|
| **Frontend** | [Streamlit](https://docs.streamlit.io/) | User interface for uploading files, asking questions, and viewing responses. |
| **Backend**  | [FastAPI](https://fastapi.tiangolo.com/) | RESTful API to handle requests from Streamlit and interface with LLMs.       |
| **LLM**      | [LiteLLM](https://github.com/litellm/litellm) | Simplified integration with GPT-4o and other LLM providers.                  |

---
##architecture:
![image](https://github.com/user-attachments/assets/8a5e0061-ff48-4637-a973-5035962c66e4)

## Project Structure

Below is the folder layout from the attached image:
ASSIGNMENT 4-1 ├── backend │ ├── pycache/ │ ├── apt.txt │ ├── llm_chat.py │ ├── main.py │ ├── pdf_extractor.py │ ├── pdf_markdown_converter.py │ ├── requirements.txt │ └── runtime.txt ├── frontend │ ├── app.py │ └── requirements.txt └── README.md

**Key Files**:
- `backend/main.py`: Entry point for the FastAPI app.
- `backend/llm_chat.py`: Manages LLM interactions (e.g., summarization, Q&A).
- `backend/pdf_extractor.py` & `backend/pdf_markdown_converter.py`: Utilities for reading and converting PDF content.
- `frontend/app.py`: Streamlit application file.
- `backend/requirements.txt` & `frontend/requirements.txt`: Python dependencies.

---

## Setup Instructions

### Local Installation

1. **Clone the Repository**
   ```bash
   git clone <YOUR_REPO_URL>
   cd ASSIGNMENT\ 4-1
# For the backend
cd backend
pip install -r requirements.txt

# Go back and install frontend requirements
cd ../frontend
pip install -r requirements.txt

#If your LLM services or any external APIs require tokens/keys, create a .env file in each folder (or a single .env in the project root) and add your API keys.

Example .env content:

bash
Copy
LLM_API_KEY="your-llm-api-key"
