import streamlit as st
import requests
import json
import time
import os
from typing import Dict, List, Any

# API Configuration
API_URL = os.environ.get("API_URL", "https://shl-project.onrender.com")
RECOMMEND_ENDPOINT = f"{API_URL}/recommend"
HEALTH_ENDPOINT = f"{API_URL}/health"

# Page configuration
st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_api_health() -> bool:
    """Check if the API is available."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def format_duration(duration: int) -> str:
    """Format duration in a readable way."""
    if not duration:
        return "Unknown"
    return f"{duration} minutes"

def get_recommendations(job_description: str) -> Dict[str, Any]:
    """Get assessment recommendations from the API."""
    try:
        response = requests.post(
            RECOMMEND_ENDPOINT,
            json={"query": job_description},
            timeout=1000,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        return {}

def display_assessment(assessment: Dict[str, Any], index: int, show_score: bool = True):
    """Display an assessment with its details."""
    assessment_data = assessment.get("assessment", assessment)

    TEST_TYPE_MAP = {
        "A": "Ability & Aptitude",
        "B": "Biodata & Situational Judgement",
        "C": "Competencies",
        "D": "Development & 360",
        "E": "Assessment Exercises",
        "K": "Knowledge & Skills",
        "P": "Personality & Behavior",
        "S": "Simulations"
    }
        
    with st.container():
        name = assessment_data.get('name', 'Assessment')
        url = assessment_data.get('url', '#')
        st.markdown(f"### [{name}]({url})")

        description = assessment_data.get('description', 'No description available')
        st.markdown(f"{description}")

        col_info1, col_info2, col_info3 = st.columns(3)

        with col_info1:
            duration = format_duration(assessment_data.get('duration', 0))
            st.markdown(f"⏱️ **Duration:** {duration}")

        with col_info2:
            remote = "✅" if assessment_data.get('remote_support') == "Yes" else "❌"
            st.markdown(f"🌐 **Remote Support:** {remote}")

        with col_info3:
            adaptive = "✅" if assessment_data.get('adaptive_support') == "Yes" else "❌"
            st.markdown(f"🔄 **Adaptive:** {adaptive}")

        test_types = assessment_data.get('test_type', [])
        if test_types:
            if isinstance(test_types, list):
                test_types_str = ", ".join(TEST_TYPE_MAP.get(t, t) for t in test_types)
            else:
                test_types_str = TEST_TYPE_MAP.get(test_types, test_types)
            st.markdown(f"🏷️ **Type(s):** {test_types_str}")
            
        st.markdown("---")

def main():
    st.title("SHL Assessment Recommender")
    st.markdown("""
    Enter a job description below, and we'll recommend the most suitable SHL assessments.
    Our AI will analyze the text and find assessments that match the job requirements.
    """)

    api_available = check_api_health()
    if not api_available:
        st.error("⚠️ API service is currently unavailable. Please try again later.")

    tab1, tab2 = st.tabs(["🔍 Recommend Assessments", "ℹ️ About"])

    with tab1:
        job_description = st.text_area(
            "Enter job description or requirements:",
            height=200,
            help="Paste a full job description or specify assessment requirements",
            placeholder="Example: We are looking for an IT Manager with 5+ years of experience in software development. The candidate should have strong leadership skills and be able to manage a team of 10 developers. They should be proficient in Agile methodologies and have experience with project management tools."
        )

        submit_button = st.button("Get Recommendations", type="primary")

        if submit_button and job_description and api_available:
            with st.spinner("🔍 Analyzing job description and fetching recommendations..."):
                start_time = time.time()
                results = get_recommendations(job_description)
                processing_time = time.time() - start_time

                if results:
                    st.success(f"Found recommendations in {processing_time:.2f} seconds")
                    
                    recommendations = results["recommendations"].get('recommended_assessments', [])
                    if not recommendations:
                        st.warning("No specific assessments found for these criteria. Try adjusting your job description.")
                    else:
                        for i, recommendation in enumerate(recommendations):
                            display_assessment(recommendation, i + 1)
                else:
                    st.error("Failed to get recommendations. Please try again or modify your job description.")

    with tab2:
        st.header("About SHL Assessment Recommender")
        st.markdown("""
        This tool helps HR professionals and recruiters find the most suitable SHL assessments for their job openings.

        ### How it works:
        1. You provide a job description or requirements  
        2. Our AI analyzes the text to extract key job characteristics  
        3. The system searches the SHL catalog for matching assessments  
        4. Results are ranked by relevance to your needs

        ### Key Features:
        - **AI-Powered Analysis**: Uses advanced language models to understand job requirements  
        - **Relevance Scoring**: Ranks assessments based on how well they match your needs  
        - **Time-Saving**: Eliminates manual searching through the SHL catalog

        For more information about SHL assessments, visit [SHL's official website](https://www.shl.com/products/product-catalog/).
        """)

if __name__ == "__main__":
    main()