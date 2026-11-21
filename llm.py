"""
llm.py
======
This module handles integration with LLM providers (Groq and Google Gemini)
using their official Python SDKs:
  - `groq` (Groq Python SDK)
  - `google-genai` (Google GenAI Python SDK)

It encapsulates prompt construction, API call handling, and JSON parsing.
"""

import json
import os
from dotenv import load_dotenv

# Try importing official SDKs with fallback indicators
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None
    GROQ_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    GEMINI_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()


def extract_json(text: str) -> dict:
    """
    Helper function to safely extract and parse JSON from a model response.
    Cleans markdown code blocks (```json ... ```) if present and validates the output.
    """
    text = text.strip()

    # Clean markdown fences if model included them
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        data = json.loads(text)

        # Enforce max 6 steps limit in python code as a safeguard
        if "steps" in data and isinstance(data["steps"], list):
            if len(data["steps"]) > 6:
                data["steps"] = data["steps"][:6]

        return data
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON output from model response: {e}\nRaw output:\n{text}"
        )


def generate_recipe(
    provider: str,
    model: str,
    temperature: float,
    max_tokens: int,
    system_prompt: str,
    ingredients: str,
    cuisine_type: str = "Any Cuisine",
    meal_type: str = "Any Meal",
    diet_pref: str = "None",
) -> dict:
    """
    Sends leftover ingredients and options to the selected LLM provider (Groq or Gemini)
    and returns a structured dictionary containing the recipe details (max 6 steps).
    """

    # Build detailed user message with user input and preferences
    user_content = f"LEFTOVER INGREDIENTS AVAILABLE:\n{ingredients}\n\n"
    user_content += f"PREFERRED CUISINE TYPE: {cuisine_type}\n"
    user_content += f"MEAL TYPE PREFERENCE: {meal_type}\n"
    user_content += f"DIETARY RESTRICTION PREFERENCE: {diet_pref}\n\n"
    user_content += "Please generate a creative, delicious recipe in 6 steps or fewer using these ingredients."

    if provider == "Groq":
        if not GROQ_AVAILABLE:
            raise ImportError(
                "The `groq` Python SDK is not installed. Please run `pip install groq`."
            )

        # 1. Retrieve API Key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing! Please set it in your .env file or environment variables."
            )

        # 2. Initialize official Groq client
        client = Groq(api_key=api_key)

        # 3. Call Groq Chat Completions API with JSON mode
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
            max_completion_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return extract_json(content)

    elif provider == "Gemini":
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "The `google-genai` Python SDK is not installed. Please run `pip install google-genai`."
            )

        # 1. Retrieve API Key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing! Please set it in your .env file or environment variables."
            )

        # 2. Initialize official Google GenAI client
        client = genai.Client(api_key=api_key)

        # 3. Combine System Prompt and User Request for Gemini
        full_prompt = f"{system_prompt}\n\n{user_content}"

        try:
            # 4. Generate content with structured JSON mime type
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    response_mime_type="application/json",
                ),
            )
            content = response.text
            return extract_json(content)

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                raise RuntimeError(
                    "Gemini Free Tier Quota Exceeded!\n"
                    "Google restricts free tier API keys to strict per-minute/per-day limits.\n"
                    "💡 Tip: Wait 30 seconds and try again, get a fresh key at https://aistudio.google.com/app/apikey, or switch Provider to 'Groq' in the sidebar for instant generation!"
                )
            elif "404" in err_msg or "NOT_FOUND" in err_msg:
                raise RuntimeError(
                    f"Model '{model}' is not available for new users on Gemini Free Tier.\n"
                    
                )
            else:
                raise e

    else:
        raise ValueError(
            f"Unsupported provider: '{provider}'. Supported providers are 'Groq' and 'Gemini'."
        )
