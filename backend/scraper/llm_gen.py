"""
@file    llm_gen.py
@brief   LLM-based generation of organization descriptions and category assignments.
@author  Adam Kinzel (xkinzea00)
"""

import json
import os

from openai import OpenAI

from utils import get_web_content


_MODEL = "gpt-4o-mini"
_TEMPERATURE = 0.2

# Categories the LLM is allowed to choose from.
# Must remain in sync with the database codebook of categories.
_AVAILABLE_CATEGORIES = (
    "Social services", "Education", "Healthcare", "Culture", "Environment",
    "Sports", "Youth", "Senior support", "Disability support",
    "Community development", "Human rights", "Charity & fundraising",
    "Arts & creative activities", "Animal welfare", "Other",
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _build_prompt(npo_name: str, web_content: str) -> str:
    """Compose the user prompt instructing the LLM to classify and describe an NPO."""
    categories_list = "\n".join(f"- {c}" for c in _AVAILABLE_CATEGORIES)
    return f"""
    You are analyzing a Czech non-profit organization strictly based on the
    information provided - its name and the content of its landing web page.

    Task:
    1) Assign 1-4 most relevant categories from the predefined list.
    2) Write a concise, neutral description (max 80 words, 3 sentences).
    3) Use only the provided information. Do not invent facts.

    Return ONLY valid JSON in this format:
    {{
      "categories": ["Category1", "Category2"],
      "description": "Short description text."
    }}

    Available categories:
    {categories_list}

    NGO data:
    Name: {npo_name}
    Web content:
    {web_content}
    """


def generate(npo_name: str, url: str) -> dict:
    """
    Generate a description and category assignment for an NPO.

    The function fetches and extracts the textual content of the provided URL
    and asks an OpenAI chat model to classify the organization and produce a
    short description.

    Returns:
        dict: JSON object with keys categories (list[str]) and description (str).
    """
    web_content = get_web_content(url)
    prompt = _build_prompt(npo_name, web_content)

    response = client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=_TEMPERATURE,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)