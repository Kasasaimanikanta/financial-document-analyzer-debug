

# Financial Document Analyzer

## Project Overview
A comprehensive financial document analysis system that processes corporate reports, financial statements, and investment documents using AI-powered analysis agents.

**Now supports:**
- Concurrent request handling with Celery and Redis (background queue worker)
- Persistent storage of analysis results and user data with SQLAlchemy (SQLite by default)

---

## Bugs Found & How They Were Fixed

### 1. LLM Not Set (Critical)
**Bug:** `llm = None` in `agents.py` caused CrewAI to fail when trying to use the LLM.

**Fix:**
```python
from crewai import LLM
import os
llm = LLM(
	model="gemini/gemini-1.5-flash-latest",
	api_key=os.getenv("GEMINI_API_KEY"),
	provider="google"
)
```
Set your Gemini API key in `.env` as `GEMINI_API_KEY=your_key_here`.

---

### 2. Wrong Install Command in README
**Bug:** README said `pip install -r requirement.txt` (wrong filename). and removed some packages names in the file crewai automatically install subpackages 

**Fix:**
```sh
pip install -r requirements.txt
```

---

### 3. Fake PDF Loader (tools.py)
**Bug:** The `Pdf` class returned fake content, not real PDF text.

**Fix:**
```python
import pdfplumber
class Pdf:
	def __init__(self, file_path):
		self.file_path = file_path
	def load(self):
		pages = []
		with pdfplumber.open(self.file_path) as pdf:
			for page in pdf.pages:
				text = page.extract_text()
				if text:
					class Page:
						def __init__(self, content):
							self.page_content = content
					pages.append(Page(text))
		return pages
```

---

### 4. Route/Task Name Collision
**Bug:** `analyze_financial_document` was both a FastAPI route and a Task, causing CrewAI to receive a function instead of a Task object.

**Fix:**
Rename the FastAPI route:
```python
@app.post("/analyze")
async def analyze_document_endpoint(...):
	...
```

---

### 5. Task Prompt Did Not Reference file_path
**Bug:** Task prompt did not instruct the agent to use `{file_path}` so the tool defaulted to a missing file.

**Fix:**
```python
analyze_financial_document = Task(
	description=(
		"Read the financial document located at {file_path} using the Financial Document Reader tool. "
		"Then answer the user's query: {query}. Provide structured financial insights."
	),
	expected_output=(
		"A structured financial analysis including:\n"
		"- Executive Summary\n"
		"- Financial Highlights\n"
		"- Key Risks\n"
		"- Investment Outlook"
	),
	agent=financial_analyst,
	tools=[financial_document_tool],
	async_execution=False,
)
```



## Setup Instructions

1. Clone the repo and navigate to the project directory.
2. Install dependencies:
	```sh
	pip install -r requirements.txt
	```
3. Create a `.env` file in the root directory:
	```env
	GEMINI_API_KEY=your_gemini_key_here
	# Optional: override DB or Redis URLs
	# DATABASE_URL=sqlite:///./financial_analyzer.db
	# CELERY_BROKER_URL=redis://localhost:6379/0
	# CELERY_RESULT_BACKEND=redis://localhost:6379/0
	```
4. (Optional) Download a sample PDF and place it in the `data/` folder.
5. **Start Redis:**
	- Download Redis for Windows: https://github.com/tporadowski/redis/releases
	- Extract and run:
	  ```sh
	  cd C:/redis
	  ./redis-server.exe
	  ```
6. **Start the Celery worker (Windows):**
	```sh
	celery -A main.celery_app worker --loglevel=info --pool=solo
	```
	- On Linux/macOS, you can omit `--pool=solo` for full parallelism.
7. **Start the FastAPI server:**
	```sh
	uvicorn main:app --reload
	```

---

## Usage Instructions


### Upload and Analyze a PDF (Async Queue)

Send a POST request to `/analyze` with a PDF file and a query. The request is queued and processed in the background.

**Python Example:**
```python
import requests
url = "http://localhost:8000/analyze"
files = {'file': open('data/TSLA-Q2-2025-Update.pdf', 'rb')}
data = {'query': 'Analyze this financial document for investment insights', 'username': 'your_username'}
response = requests.post(url, files=files, data=data)
print(response.json())  # {'status': 'processing', 'task_id': '...'}

# Later, poll for result:
task_id = response.json()["task_id"]
result = requests.get(f"http://localhost:8000/result/{task_id}")
print(result.json())
```

**Curl Example:**
```sh
curl -X POST "http://localhost:8000/analyze" \
	-F "file=@data/TSLA-Q2-2025-Update.pdf" \
	-F "query=Analyze this financial document for investment insights" \
	-F "username=your_username"

# Poll for result
curl http://localhost:8000/result/<task_id>
```

---

## API Documentation


### API Documentation

#### POST /analyze
**Description:**
Queue a financial PDF for analysis. Returns a task ID for polling.

**Request:**
- `file`: PDF file (required)
- `query`: Analysis query (optional)
- `username`: User identifier (optional)

**Response:**
```
{
	"status": "processing",
	"task_id": "...",
	"file_processed": "TSLA-Q2-2025-Update.pdf"
}
```

#### GET /result/{task_id}
**Description:**
Poll for the result of an analysis task.

**Response:**
```
{
	"status": "success",
	"analysis": "..."
}
```

#### GET /user/{username}/analyses
**Description:**
Get all analysis results for a user (from the database).

**Response:**
```
[
	{
		"query": "...",
		"analysis": "...",
		"file_path": "...",
		"created_at": "..."
	},
	...
]
```

---


## Additional Notes

- Make sure your `.env` file is correct and your API key is valid.
- If using Gemini, set `provider="google"` in your LLM config.
- For production, run Celery on Linux for full parallelism (Windows: use `--pool=solo`).
- For multi-agent or advanced workflows, see CrewAI documentation.
- Database is SQLite by default; you can use PostgreSQL or MySQL by changing `DATABASE_URL` in `.env`.
