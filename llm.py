"""
Gemini API integration using google-genai (new package).

This module provides a reusable interface for interacting with Google's Gemini LLM.
"""

import os
from typing import Optional
from google import genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def configure_gemini() -> None:
    """
    Configure the Gemini API with the API key from environment variables.
    
    Raises:
        ValueError: If GEMINI_API_KEY environment variable is not set.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )


def ask_llm(prompt: str, model: str = "gemini-2.5-flash") -> Optional[str]:
    """
    Send a prompt to the Gemini API and return the clean text response.
    
    Args:
        prompt (str): The prompt to send to the Gemini model.
        model (str): The model to use (default: gemini-2.5-flash).
    
    Returns:
        Optional[str]: The text response from the model, or None if an error occurs.
    
    Raises:
        ValueError: If Gemini is not configured before calling this function.
    """
    try:
        # Initialize the Gemini model
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Send the prompt and get response
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        
        # Extract and return clean text
        if response and response.text:
            return response.text.strip()
        else:
            return None
            
    except ValueError as e:
        print(f"Configuration error: {e}")
        return None
    except Exception as e:
        print(f"Error calling Gemini API: {type(e).__name__} - {e}")
        return None


def list_available_models() -> list:
    """
    List all available Gemini models.
    
    Returns:
        list: A list of available model names.
    """
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        models = client.models.list()
        return [model.name for model in models]
    except Exception as e:
        print(f"Error listing models: {type(e).__name__} - {e}")
        return []


# Initialize Gemini configuration on module import
try:
    configure_gemini()
except ValueError as e:
    print(f"Warning: {e}")


# ============================================================================
# Test Example
# ============================================================================
if __name__ == "__main__":
    # Test prompt
    test_prompt = "who will win in the upcoming ufc fight between khamzat and strickland?"  # Example prompt for testing
    
    # Call the LLM
    response = ask_llm(test_prompt)
    
    if response:
        print(response)
    else:
        print("Failed to get response from Gemini API.")
