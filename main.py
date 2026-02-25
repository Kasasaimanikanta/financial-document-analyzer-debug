
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid
from celery import Celery
from sqlalchemy.orm import Session
from db import SessionLocal, AnalysisResult, User
from crewai import Crew, Process
from agents import financial_analyst
from task import analyze_financial_document

app = FastAPI(title="Financial Document Analyzer")

# Celery configuration
celery_app = Celery(
    "worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """To run the whole crew"""
    financial_crew = Crew(
        agents=[financial_analyst],
        tasks=[analyze_financial_document],
        process=Process.sequential,
    )
    result = financial_crew.kickoff({'file_path': file_path, 'query': query})
    return result

@celery_app.task
def analyze_document_task(query: str, file_path: str, username: str = None):
    result = run_crew(query, file_path)
    # Save to DB
    db = SessionLocal()
    analysis = AnalysisResult(
        query=query,
        analysis=str(result),
        file_path=file_path,
        username=username
    )
    db.add(analysis)
    db.commit()
    db.close()
    return str(result)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}

@app.post("/analyze")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights"),
    username: str = Form(default=None)
):
    """Analyze financial document and provide comprehensive investment recommendations (async via Celery)"""
    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"
    try:
        os.makedirs("data", exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        if not query:
            query = "Analyze this financial document for investment insights"
        # Enqueue Celery task
        task = analyze_document_task.delay(query.strip(), file_path, username)
        return {"status": "processing", "task_id": task.id, "file_processed": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing financial document: {str(e)}")

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.state == "PENDING":
        return {"status": "pending"}
    elif result.state == "SUCCESS":
        return {"status": "success", "analysis": result.result}
    elif result.state == "FAILURE":
        return {"status": "failed", "error": str(result.result)}
    else:
        return {"status": result.state.lower()}

@app.get("/user/{username}/analyses")
async def get_user_analyses(username: str):
    db = SessionLocal()
    results = db.query(AnalysisResult).filter(AnalysisResult.username == username).all()
    db.close()
    return [{"query": r.query, "analysis": r.analysis, "file_path": r.file_path, "created_at": r.created_at.isoformat()} for r in results]