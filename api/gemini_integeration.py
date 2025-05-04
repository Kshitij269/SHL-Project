import os
import google.generativeai as genai
import re
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

JOB_FAMILY_MAP = {
    "sales": "Sales",
    "it": "Information Technology",
    "tech": "Information Technology",
    "information technology": "Information Technology",
    "software": "Information Technology",
    "business": "Business",
    "clerical": "Clerical",
    "administrative": "Clerical",
    "contact center": "Contact Center",
    "call center": "Contact Center",
    "customer service": "Customer Service",
    "customer support": "Customer Service",
    "safety": "Safety",
    "security": "Safety",
}

JOB_LEVEL_MAP = {
    "graduate": "Graduate",
    "entry-level": "Entry-Level",
    "entry level": "Entry-Level",
    "junior": "Entry-Level",
    "executive": "Executive",
    "c-level": "Executive",
    "director": "Director",
    "front line manager": "Front Line Manager",
    "frontline manager": "Front Line Manager",
    "first line manager": "Front Line Manager",
    "manager": "Manager",
    "mid-professional": "Mid-Professional",
    "mid professional": "Mid-Professional",
    "professional individual contributor": "Professional Individual Contributor",
    "individual contributor": "Professional Individual Contributor",
    "supervisor": "Supervisor",
    "general population": "General Population",
    "general": "General Population",
}

INDUSTRY_MAP = {
    "banking": "Banking/Finance",
    "finance": "Banking/Finance",
    "financial": "Banking/Finance",
    "bank": "Banking/Finance",
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "medical": "Healthcare",
    "hospitality": "Hospitality",
    "hotel": "Hospitality",
    "restaurant": "Hospitality",
    "insurance": "Insurance",
    "manufacturing": "Manufacturing",
    "factory": "Manufacturing",
    "production": "Manufacturing",
    "oil": "Oil & Gas",
    "gas": "Oil & Gas",
    "energy": "Oil & Gas",
    "petroleum": "Oil & Gas",
    "retail": "Retail",
    "store": "Retail",
    "shop": "Retail",
    "telecommunications": "Telecommunications",
    "telecom": "Telecommunications",
    "communication": "Telecommunications",
}

LANGUAGE_MAP = {
    "english": "English",
    "en": "English",
    "french": "French",
    "fr": "French",
    "german": "German",
    "de": "German",
    "spanish": "Spanish",
    "es": "Spanish",
}


class GeminiQueryParser:
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "Gemini API key is required. Provide it directly or set GEMINI_API_KEY environment variable."
            )

        genai.configure(api_key=api_key)

        self.model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

        logger.info("Gemini GenerativeModel initialized")

    def parse_query(self, query: str) -> Dict[str, Any]:
        logger.info(f"Parsing query with Gemini: {query[:50]}...")
        prompt = self._build_prompt(query)

        try:
            response = self.model.generate_content(prompt)

            filters_text = response.text.strip()
            logger.debug(f"Raw Gemini response: {filters_text}")

            if filters_text:
                return self._parse_filters(filters_text)
            else:
                logger.error("Empty response from Gemini API")
                return {}

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise

    def _build_prompt(self, query: str) -> str:
        return f"""
        # Job Description Analysis
        You are solving this problem consider yourself as Hiring managers who often struggle to find the right assessments for the roles that they are hiring for. The current
        system relies on keyword searches and filters, making the process time-consuming and inefficient. Your task
        is to build an intelligent recommendation system that simplifies this process. Given a natural language
        query or a job description text or URL, your application should return a list of relevant SHL assessments.
        and now you will help to extract specific technical assessment criteria from the following job description:

        ## Job Description:
        "{query}"

        ## Task:
        First please try to understand the context of the job description and then extract the relevant information from it.
        My task is to identify the CORE TECHNICAL COMPETENCIES and other specific information needed for selecting appropriate assessment tools.

        ## Analysis Results:

        Keywords: [
            For examples for sales type keyowrds can be Sales , Strategy , Product , Marketing etc.
            For examples for IT type keyowrds can be Python , Java , C++ etc.
            For examples for healthcare type keyowrds can be Nursing , Medical , Healthcare etc.
            For examples for manufacturing type keyowrds can be Production , Factory , Manufacturing etc.
            For examples for hospitality type keyowrds can be Hotel , Restaurant , Hospitality etc.
            For examples for banking type keyowrds can be Banking , Finance , Financial etc.
            I will first understand the context of what my query is talking about e.g if it is like sales domain then keyword can be Sales etc.
            I will extract 2-3 specific technical keywords that can be directly assessed.
            I will focus PRIMARILY on extracting TECHNICAL and DOMAIN-SPECIFIC keywords
            I will ignore soft skills and generic competencies when selecting keywords
            These must be precise, assessable competencies like "Python", "Financial Modeling", "Network Security", "Salesforce CRM", or "Supply Chain Management". 
            I will NOT use generic terms like "communication" or "teamwork" .
            I will extract EXACTLY 2-3 SPECIFIC technical skills, tools, or knowledge areas that are CENTRAL to performing this job and these would be seprated by comma(,).  I will return as text not array. Each keyword will be comprised of only single word]

        Job Family: [ONLY SELECT ONE FROM: Business, Clerical, Contact Center, Customer Service, Information Technology, Safety, Sales]

        Job Level: [
        new-graduates are called entry level, and they are not called as graduate.
        ONLY SELECT ONE FROM: Entry-Level, Front Line Manager, Mid-Professional, Professional Individual Contributor, Supervisor, Manager, Director, Executive, Graduate, General Population]

        Industry: [ONLY SELECT ONE FROM: Banking/Finance, Healthcare, Hospitality, Insurance, Manufacturing, Oil & Gas, Retail, Telecommunications]  

        Language: [
            "Arabic",
            "Bulgarian",
            "Chinese Simplified",
            "Chinese Traditional",
            "Croatian",
            "Czech",
            "Danish",
            "Dutch",
            "English (Australia)",
            "English (Canada)",    
            "English International",        
            "English (Malaysia)",
            "English (Singapore)", 
            "English (South Africa)",
            "English (USA)",
            "Estonian",
            "Finnish",
            "Flemish",
            "French",
            "French (Belgium)",
            "French (Canada)",
            "German",
            "Greek",
            "Hungarian",
            "Icelandic",
            "Indonesian",
            "Italian",
            "Japanese",
            "Korean",
            "Latin American Spanish",
            "Latvian",
            "Lithuanian",
            "Malay",
            "Norwegian",
            "Polish",
            "Portuguese",
            "Portuguese (Brazil)",
            "Romanian",
            "Russian",
            "Serbian",
            "Slovak",
            "Spanish",
            "Swedish",
            "Thai",
            "Turkish",
            "Vietnamese"
        ]

        Duration: [Test duration in minutes based on complexity of role]

        Notes: [Additional relevant details such as remote work capability, specialized skills, etc. . I will return as text not array]

        ## Special Instructions:
        - Don't Mention things like this "keywords": "Prospecting,Closing" for example if the context is of Sales then Keyword can be Sales , etc related to context
        - Each keywords will comprise of single word only
        - I will focus PRIMARILY on extracting TECHNICAL and DOMAIN-SPECIFIC keywords
        - I will ALWAYS provide 2-3 specific technical keywords that can be directly assessed
        - I will IGNORE soft skills and generic competencies when selecting keywords
        - Keywords must not include any general things like "Development" , "Tools" , "Prospecting" , "Closing" , "Qualification"
        - Keywords must be SPECIFIC (e.g., "Java" not just "Programming")
        - For other categories where information is not clearly provided, I will leave the field empty
        - I will ONLY use the exact category values listed above for Job Family, Job Level, Industry, and Language
        - Each keyword should represent a distinct skill or competency area that can be tested

        """

    def _normalize_value(
        self, value: str, mapping_dict: Optional[Dict[str, str]] = None
    ) -> str:
        if not value:
            return ""

        value = re.sub(r"[\"'\[\]]", "", value)
        value = re.sub(r"\(.*?\)", "", value).strip().lower()

        if not value or value in ["none", "n/a", "not specified", "unknown"]:
            return ""

        if mapping_dict:
            for k, v in mapping_dict.items():
                if k == value or k in value.split():
                    return v

        return value.title()

    def _parse_filters(self, filters_text: str) -> Dict[str, Any]:
        filters = {}

        lines = filters_text.strip().splitlines()

        current_section = None
        keywords_list = []

        for line in lines:
            clean_line = re.sub(r"^[\-\*\•\–\—\u2022\s]+", "", line).strip()
            clean_line = re.sub(r"\\", "", clean_line)

            if ":" in clean_line:
                key, value = clean_line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                current_section = key

                if not value or value.lower() in [
                    "none",
                    "n/a",
                    "not specified",
                    "unknown",
                ]:
                    continue

                if key == "keywords":
                    if value and not re.match(r"^\d+\.", value):
                        keywords_list = [value]
                elif key == "job family":
                    normalized_value = self._normalize_value(value, JOB_FAMILY_MAP)
                    if normalized_value:
                        filters["job_family"] = normalized_value
                elif key == "job level":
                    normalized_value = self._normalize_value(value, JOB_LEVEL_MAP)
                    if normalized_value:
                        filters["job_level"] = normalized_value
                elif key == "industry":
                    normalized_value = self._normalize_value(value, INDUSTRY_MAP)
                    if normalized_value:
                        filters["industry"] = normalized_value
                elif key == "language":
                    normalized_value = self._normalize_value(value, LANGUAGE_MAP)
                    if normalized_value:
                        filters["language"] = normalized_value
                elif key == "duration":

                    duration_match = re.search(
                        r"(\d+)(?:\s*-\s*\d+)?\s*min", value.lower()
                    )
                    if duration_match:
                        filters["duration"] = duration_match.group(1) + " minutes"
                    else:
                        filters["duration"] = re.sub(r"[\"']", "", value).strip()
                elif "notes" in key or "relevant details" in key:
                    filters["notes"] = re.sub(r"[\"']", "", value).strip()

            elif current_section == "keywords":
                numbered_item = re.match(r"^\s*\d+\.\s*(.*)", clean_line)
                if numbered_item:
                    keyword = numbered_item.group(1).strip()
                    if keyword and not keyword.lower() in [
                        "none",
                        "n/a",
                        "not specified",
                        "unknown",
                    ]:
                        keywords_list.append(keyword)

        if keywords_list:
            filters["keywords"] = ", ".join(keywords_list)

        logger.info(f"Extracted filters: {json.dumps(filters, indent=2)}")
        return filters


def parse_query_with_gemini(query: str) -> Dict[str, Any]:
    try:
        parser = GeminiQueryParser()
        return parser.parse_query(query)
    except Exception as e:
        logger.error(f"Error parsing query: {str(e)}")
        return {}
