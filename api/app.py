import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import time
import json
from api.gemini_integeration import parse_query_with_gemini
from api.gemini_recommender import get_top_assessments_with_gemini
from api.shl_scraper import fetch_assessments, save_assessments

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SHL Assessment Recommender API",
    description="API for recommending SHL assessments based on job descriptions",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*" , "https://shl-assessments.streamlit.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class HealthResponse(BaseModel):
    status: str
    version: str


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/recommend")
def recommend(query: QueryRequest):
    try:
        start_time = time.time()

        if not query.query or len(query.query.strip()) < 10:
            raise HTTPException(status_code=400)

        filters = parse_query_with_gemini(query.query)

        if not filters:
            logger.warning("No filters were extracted from the job description")
            return {
                "filters": {},
                "recommendations": [],
                "message": "Could not extract search criteria from job description",
            }

        raw_results = fetch_assessments(filters)

        recommendations = save_assessments(raw_results)

        results = get_top_assessments_with_gemini(query.query, k=10)

        with open("recommendationsResponse.txt", "w", encoding="utf-8") as file:
            json.dump(
                {
                    "recommendations": results,
                },
                file,
                indent=2,
            )

        processing_time = time.time() - start_time

        return {
            "recommendations": results,
        }

    except Exception as e:
        logger.error(f"Error processing recommendation: {str(e)}")
        raise HTTPException(status_code=500)


if __name__ == "_main_":
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000)
