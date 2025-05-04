import os
import json
import google.generativeai as genai
import re

api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

def extract_valid_json(response_text):
    try:
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in response.")
        json_str = json_match.group(0)
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", str(e))
        return {}


def load_assessments(json_path="assessments_data.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fix_recommended_assessments_json(response_json: dict) -> dict:
    required_fields = {
        "url": str,
        "adaptive_support": str,
        "description": str,
        "duration": int,
        "remote_support": str,
        "test_type": list,
    }

    fixed_assessments = []
    assessments = response_json.get("recommended_assessments", [])

    for assessment in assessments:
        if not isinstance(assessment, dict):
            continue

        cleaned = {}

        try:
            for key, expected_type in required_fields.items():
                if key not in assessment:
                    raise ValueError(f"Missing key: {key}")
                value = assessment[key]

                if expected_type == str:
                    cleaned[key] = str(value).strip()
                elif expected_type == int:
                    cleaned[key] = int(value)
                elif expected_type == list:
                    if isinstance(value, list):
                        cleaned[key] = [str(v).strip() for v in value]
                    else:
                        cleaned[key] = [str(value).strip()]
            fixed_assessments.append(cleaned)

        except Exception as e:
            print(f"Skipping malformed assessment: {e}")
            continue

    return {"recommended_assessments": fixed_assessments}


def get_top_assessments_with_gemini(user_query, k=10):
    model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

    assessments = load_assessments()
    prompt = f"""
You are an intelligent assessment recommender first understand the context then proceedए.

Given a user's job description or query, and a catalog of assessments,
recommend at most {k} of the most relevant assessments.

Return only a valid JSON object with this exact format:
{{
  "recommended_assessments": [
    {{
      "url": "...",
      "adaptive_support": "Yes" or "No",
      "description": "...",
      "duration": integer,
      "remote_support": "Yes" or "No",
      "test_type": [list of strings]
    }},
    ...
  ]
}}

The JSON object should contain a list of recommended assessments.
You must not include any other text or explanation. Please do not add any additional information or context.
Do not include any markdown, code block formatting, or extra commentary.
Only use this format to return the JSON object. Do not deviate from this format.

Input Query:
"{user_query}"

Assessment Catalog:
{json.dumps(assessments)}
"""

    response = model.generate_content(prompt)
    response_text = response.text if hasattr(response, "text") else str(response)
    response_text = re.sub(r"```(json)?", "", response_text).strip()

    with open("gemini_response.txt", "w", encoding="utf-8") as file:
        file.write(response_text)

    try:
        raw_json = json.loads(response_text)
    except json.JSONDecodeError:
        raw_json = extract_valid_json(response_text)

    return fix_recommended_assessments_json(raw_json)
