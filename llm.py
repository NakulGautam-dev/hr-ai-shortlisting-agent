"""
Gemini API integration.

Reusable interface for interacting with Google's Gemini LLM.
"""

import os
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY not found in environment variables."
    )

# Configure Gemini
genai.configure(api_key=api_key)


def ask_llm(
    prompt: str,
    model: str = "models/gemini-2.5-flash"
) -> Optional[str]:
    """
    Send prompt to Gemini and return response text.
    """

    try:
        # Initialize model
        gemini_model = genai.GenerativeModel(model_name=model)

        # Generate response
        response = gemini_model.generate_content(prompt)

        # Return clean text
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()

        return None

    except Exception as e:
        print(f"Error calling Gemini API: {type(e).__name__} - {e}")
        return None


def list_available_models() -> list:
    """
    List available Gemini models.
    """

    try:
        models = genai.list_models()

        available_models = []

        for model in models:
            available_models.append(model.name)

        return available_models

    except Exception as e:
        print(f"Error listing models: {type(e).__name__} - {e}")
        return []


if __name__ == "__main__":

    print("Testing Gemini API...\n")

    # Show available models
    print("Available Models:\n")

    models = list_available_models()

    for model in models:
        print(model)

    print("\n----------------------------------\n")

    test_prompt = "Hello Gemini"

    response = ask_llm(test_prompt)

    if response:
        print("Response:\n")
        print(response)

    else:
        print("Failed to get response from Gemini.")