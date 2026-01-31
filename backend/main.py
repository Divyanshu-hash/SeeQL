from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from sql_explainer import explain_sql
from error_translator import translate_error
from sqlalchemy import text
from database import engine
from sample_data import insert_sample_data
import pandas as pd
import uuid
import os
import io

app = FastAPI(title="SeeQL — Visual SQL Learning Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Dataset metadata for built-in datasets
DATASET_META = {
    "students": {
        "name": "Students",
        "description": "A small table of students and their marks. Great for practicing SELECT, WHERE, and ORDER BY.",
        "table_name": "students",
        "example_queries": [
            "SELECT * FROM students",
            "SELECT name, marks FROM students WHERE marks > 80",
            "SELECT * FROM students ORDER BY marks DESC",
        ],
        "learning_goals": ["Filter by marks (WHERE)", "Sort by a column (ORDER BY)", "Pick specific columns (SELECT)"],
    },
    "employees": {
        "name": "Employees",
        "description": "Employees with department and salary. Perfect for filtering and comparing data.",
        "table_name": "employees",
        "example_queries": [
            "SELECT * FROM employees",
            "SELECT name, department FROM employees WHERE department = 'IT'",
            "SELECT * FROM employees ORDER BY salary DESC",
        ],
        "learning_goals": ["Filter by department", "Sort by salary", "Compare numbers with WHERE"],
    },
    "titanic": {
        "name": "Titanic",
        "description": "Classic passenger data from the Titanic: survival, class, age, sex, and more. Ideal for real-world-style queries.",
        "table_name": "titanic",
        "example_queries": [
            "SELECT * FROM titanic LIMIT 10",
            "SELECT Name, Sex, Age, Survived FROM titanic WHERE Survived = 1",
            "SELECT Pclass, COUNT(*) FROM titanic GROUP BY Pclass",
        ],
        "learning_goals": ["Filter survivors", "Group and count (GROUP BY)", "Combine conditions with AND/OR"],
    },
    "iris": {
        "name": "Iris",
        "description": "Famous flower dataset: sepal and petal measurements for three iris species. Great for numbers and grouping.",
        "table_name": "iris",
        "example_queries": [
            "SELECT * FROM iris LIMIT 10",
            "SELECT species, AVG(sepal_length) FROM iris GROUP BY species",
            "SELECT * FROM iris WHERE species = 'setosa'",
        ],
        "learning_goals": ["Filter by species", "Use AVG and GROUP BY", "Compare measurements"],
    },
}


def load_titanic_and_iris():
    """Load Titanic and Iris from public CSV URLs into SQLite."""
    try:
        titanic_url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv"
        iris_url = "https://raw.githubusercontent.com/uiuc-cse/data-fa14/gh-pages/data/iris.csv"
        df_t = pd.read_csv(titanic_url)
        df_i = pd.read_csv(iris_url)
        # Normalize iris column names (some CSVs use spaces)
        df_i.columns = [c.strip().replace(" ", "_").lower() for c in df_i.columns]
        if "species" not in df_i.columns and len(df_i.columns) >= 5:
            df_i.columns = ["sepal_length", "sepal_width", "petal_length", "petal_width", "species"]
        df_t.to_sql("titanic", engine, index=False, if_exists="replace")
        df_i.to_sql("iris", engine, index=False, if_exists="replace")
    except Exception:
        # Fallback: create small iris/titanic tables so app still works
        fallback_iris = pd.DataFrame({
            "sepal_length": [5.1, 4.9, 7.0],
            "sepal_width": [3.5, 3.0, 3.2],
            "petal_length": [1.4, 1.4, 4.7],
            "petal_width": [0.2, 0.2, 1.4],
            "species": ["setosa", "setosa", "versicolor"],
        })
        fallback_titanic = pd.DataFrame({
            "PassengerId": [1, 2, 3],
            "Survived": [0, 1, 1],
            "Pclass": [3, 1, 3],
            "Name": ["Braund", "Cumings", "Heikkinen"],
            "Sex": ["male", "female", "female"],
            "Age": [22.0, 38.0, 26.0],
        })
        fallback_iris.to_sql("iris", engine, index=False, if_exists="replace")
        fallback_titanic.to_sql("titanic", engine, index=False, if_exists="replace")


@app.on_event("startup")
def startup():
    insert_sample_data(engine)
    load_titanic_and_iris()


@app.get("/create-session")
def create_session():
    user_id = str(uuid.uuid4())[:8]
    return {"user_id": user_id}


# -------------------------------
# List sample datasets with metadata
# -------------------------------
@app.get("/sample-datasets")
def get_sample_datasets():
    return {"datasets": ["students", "employees", "titanic", "iris"]}


@app.get("/datasets")
def get_datasets_with_metadata():
    """Return all built-in datasets with description, columns, row count."""
    result = []
    with engine.connect() as conn:
        for key in ["students", "employees", "titanic", "iris"]:
            meta = DATASET_META.get(key, {})
            table_name = meta.get("table_name", key)
            try:
                r = conn.execute(text(f"SELECT COUNT(*) as c FROM {table_name}"))
                row_count = r.scalar() or 0
                r2 = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 1"))
                columns = list(r2.keys()) if r2 else []
            except Exception:
                row_count = 0
                columns = []
            result.append({
                "id": key,
                "name": meta.get("name", key),
                "description": meta.get("description", ""),
                "table_name": table_name,
                "row_count": row_count,
                "columns": columns,
                "example_queries": meta.get("example_queries", []),
                "learning_goals": meta.get("learning_goals", []),
            })
    return {"datasets": result}


@app.get("/dataset/{table_name}/data")
def get_dataset_data(table_name: str):
    """Return full table data for a built-in or uploaded table."""
    # Allow only alphanumeric and underscore
    if not table_name.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid table name")
    if table_name.startswith("user_") or table_name in ("students", "employees", "titanic", "iris"):
        pass
    else:
        raise HTTPException(status_code=404, detail="Unknown dataset")
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            rows = [dict(row._mapping) for row in result]
        return {"rows": rows, "row_count": len(rows), "columns": list(rows[0].keys()) if rows else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dataset/{dataset_id}/meta")
def get_dataset_meta(dataset_id: str):
    """Return metadata for one dataset (description, examples, goals)."""
    meta = DATASET_META.get(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return meta


# -------------------------------
# Upload CSV dataset
# -------------------------------
@app.post("/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.csv")
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read CSV: {str(e)}")

    table_name = f"user_{file_id[:8]}"
    df.to_sql(table_name, engine, index=False, if_exists="replace")

    return {
        "message": "Dataset uploaded successfully",
        "table_name": table_name,
        "dataset_id": table_name,
        "name": file.filename.replace(".csv", ""),
        "columns": list(df.columns),
        "row_count": len(df),
    }


# -------------------------------
# Run SQL Query
# -------------------------------
@app.post("/run-query")
def run_query(body: dict = Body(...)):
    query = (body or {}).get("query", "")
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    forbidden = ["DROP", "DELETE", "UPDATE", "ALTER", "INSERT", "TRUNCATE"]
    q_upper = query.upper()
    if any(word in q_upper for word in forbidden):
        raise HTTPException(status_code=403, detail="This type of query is not allowed in the playground.")

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result]
        return {"rows": rows, "row_count": len(rows)}
    except Exception as e:
        explanation = translate_error(str(e))
        return {
            "error": True,
            "error_explanation": explanation,
            "raw_error": str(e),
        }


# -------------------------------
# Explain query (step-by-step)
# -------------------------------
@app.post("/explain-query")
def explain_query(body: dict = Body(...)):
    query = (body or {}).get("query", "")
    if not query or not query.strip():
        return {"steps": ["Enter a SQL query to see an explanation."]}
    steps = explain_sql(query)
    return {"steps": steps}


# -------------------------------
# Export result as CSV or JSON
# -------------------------------
@app.post("/export")
def export_result(body: dict = Body(...)):
    """Export the last query result. Expects { \"query\": \"...\", \"format\": \"csv\" | \"json\" }."""
    query = (body or {}).get("query", "")
    fmt = (body or {}).get("format", "csv").lower()
    if fmt not in ("csv", "json"):
        fmt = "csv"
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    forbidden = ["DROP", "DELETE", "UPDATE", "ALTER", "INSERT", "TRUNCATE"]
    if any(w in query.upper() for w in forbidden):
        raise HTTPException(status_code=403, detail="This query is not allowed.")

    try:
        df = pd.read_sql_query(query, engine)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if fmt == "json":
        return JSONResponse(content=df.to_dict(orient="records"))

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=seeql-export.csv"},
    )
