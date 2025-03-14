import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = "AIzaSyDseYE1Io995FEXahokfO8eNnDwVV856ME" #replace with the correct api key
genai.configure(api_key=api_key)

for m in genai.list_models():
    print(m)