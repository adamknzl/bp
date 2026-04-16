from utils import get_web_content

import os
import json

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate(npo_name, url):
    prompt = f"""
    You are analyzing a Czech non-profit organization strictly based on information provided - name and content from the organization's landing web page.

    Task:
    1) Assign 1-4 most relevant categories from the predefined list.
    2) Write a concise, neutral description (max 80 words, 3 sentences).
    3) Use only provided information. Do not invent facts.

    Return ONLY valid JSON in this format:
    {{
    "categories": ["Category1", "Category2"],
    "description": "Short description text."
    }}

    Available categories:
    - Social services
    - Education
    - Healthcare
    - Culture
    - Environment
    - Sports
    - Youth
    - Senior support
    - Disability support
    - Community development
    - Human rights
    - Charity & fundraising
    - Arts & creative activities
    - Animal welfare
    - Other

    NGO data:
    Name: {npo_name}
    Web content:
    {get_web_content(url)}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={ "type": "json_object" }
    )

    response_json = json.loads(response.choices[0].message.content)

    return response_json