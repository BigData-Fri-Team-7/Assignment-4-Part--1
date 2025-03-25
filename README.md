# Assignment 4 Part 1 – Streamlit & FastAPI LLM Integration


## Project Overview

This project enhances the functionality of Assignment 1 by introducing:
- A **Streamlit** frontend for uploading or selecting PDF files.
- A **FastAPI** backend that processes the PDF content, handles summarization, and answers questions using various Large Language Models (LLMs) via **LiteLLM**.
- A demonstration of token pricing, error handling, and logging for LLM interactions.

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

## Project Structure

Below is the folder layout from the attached image:
ASSIGNMENT 4-1 ├── backend │ ├── pycache/ │ ├── apt.txt │ ├── llm_chat.py │ ├── main.py │ ├── pdf_extractor.py │ ├── pdf_markdown_converter.py │ ├── requirements.txt │ └── runtime.txt ├── frontend │ ├── app.py │ └── requirements.txt └── README.md
