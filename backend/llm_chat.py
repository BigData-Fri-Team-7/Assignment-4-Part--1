#backend/llm_chat.py

import os
import tiktoken
import litellm
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI
import anthropic

# Load API keys from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
CLAUDE_API_KEY= os.getenv("CLAUDE_API_KEY")

# Configure LiteLLM for OpenAI (for GPT‑4o)
litellm.api_key = OPENAI_API_KEY

# Configure DeepSeek API client
deepseek_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def count_tokens(text: str, model: str) -> int:
    """
    Count tokens using tiktoken if supported.
    For Gemini and Claude models, use an approximate method (word count) as a fallback.
    For DeepSeek, use an explicit encoding.
    """
    try:
        if "gemini" in model.lower() or "claude" in model.lower():
            return len(text.split())
        elif "deepseek" in model.lower():
            # Explicitly use a known encoding for DeepSeek, e.g., "cl100k_base"
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        else:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
    except Exception as e:
        print(f"Token count error: {e}")
        return 0


def build_prompt(pdf_data: dict, question: str) -> str:
    """
    Constructs a prompt using the extracted PDF content and the user's question.
    """
    return f"""
You are a helpful assistant. Use the following document content to answer the question.

Document Content:
{pdf_data.get("pdf_content", "No document content available.")}

Tables Extracted:
{pdf_data.get("tables", "No tables available.")}

User Question:
{question}

Answer the question based solely on the document above.
"""

def get_llm_response(pdf_data: dict, question: str, llm_choice: str) -> str:
    """
    Builds a prompt and calls the selected LLM.
    Supports:
      - GPT-4o via LiteLLM
      - Gemini Flash Free via google.generativeai
      - DeepSeek Chat via OpenAI API wrapper
      - Claude 3.5 Haiku via Anthropic
    """
    prompt_text = build_prompt(pdf_data, question)

    try:
        if llm_choice.lower() == "gpt-4o":
            token_count = count_tokens(prompt_text, model="gpt-4o-mini-2024-07-18")
            print(f"Token count for prompt: {token_count}")

            response = litellm.completion(
                model="gpt-4o-mini-2024-07-18",
                messages=[{"role": "user", "content": prompt_text}]
            )
            return response["choices"][0]["message"]["content"]

        elif llm_choice.lower() == "gemini flash free":
            token_count = count_tokens(prompt_text, model="gemini-1.5-pro-latest")
            print(f"Token count for prompt (Gemini): {token_count}")

            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            response = model.generate_content(prompt_text)
            return response.text

        elif llm_choice.lower() in ["deepseek", "deepseek chat"]:
            token_count = count_tokens(prompt_text, model="deepseek-chat")
            print(f"Token count for prompt (DeepSeek): {token_count}")

            response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt_text},
                ],
                stream=False
            )
            return response.choices[0].message.content

        elif llm_choice.lower() in ["claude", "claude-3", "claude-3.5 haiku"]:
            token_count = count_tokens(prompt_text, model="claude-3-5-haiku-20241022")
            print(f"Token count for prompt (Claude 3.5 Haiku): {token_count}")

            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt_text}]
            )
            return response.content

        else:
            return "LLM choice not recognized."

    except Exception as e:
        print(f"Error processing request: {e}")
        return f"Error: {e}"
