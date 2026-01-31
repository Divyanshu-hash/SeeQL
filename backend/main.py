from fastapi import FastAPI, UploadFile, File, HTTPException
from sql_explainer import explain_sql_langchain
from error_translator import translate_error_langchain
from sqlalchemy import text
from database import engine
from sample_data import insert_sample_data
import pandas as pd
import uuid
import os

app = FastAPI(title="Visual SQL Learning Backend")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load sample datasets on startup
@app.on_event("startup")
def startup():
    insert_sample_data(engine)


@app.get("/create-session")
def create_session():
    user_id = str(uuid.uuid4())[:8]
    return {
        "user_id": user_id
    }

# -------------------------------
# List sample datasets
# -------------------------------
@app.get("/sample-datasets")
def get_sample_datasets():
    return {
        "datasets": ["students", "employees"]
    }

# -------------------------------
# Upload CSV dataset
# -------------------------------
@app.post("/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.csv")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    df = pd.read_csv(file_path)
    table_name = f"user_{file_id[:8]}"
    df.to_sql(table_name, engine, index=False, if_exists="replace")

    return {
        "message": "Dataset uploaded successfully",
        "table_name": table_name,
        "columns": list(df.columns)
    }

# -------------------------------
# Run SQL Query
# -------------------------------
@app.post("/run-query")
def run_query(query: str):
    forbidden = ["DROP", "DELETE", "UPDATE", "ALTER"]
    if any(word in query.upper() for word in forbidden):
        raise HTTPException(status_code=403, detail="Dangerous query blocked")

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result]

        return {
            "rows": rows,
            "row_count": len(rows)
        }

    except Exception as e:
        explanation = translate_error_langchain(str(e))
        return {
            "error_explanation": explanation,
            "raw_error": str(e),
            "source": "langchain-groq"
        }
# -------------------------------
# Export Query Result
# -------------------------------
@app.post("/export")
def export_query(query: str, format: str = "csv"):
    df = pd.read_sql_query(query, engine)

    if format == "json":
        return df.to_dict(orient="records")

    file_name = f"export.{format}"
    df.to_csv(file_name, index=False)

    return {
        "message": "Export successful",
        "file": file_name
    }


@app.post("/explain-query")
def explain_query(query: str):
    steps = explain_sql_langchain(query)
    return {
        "steps": steps,
        "method": "langchain-groq"
    }