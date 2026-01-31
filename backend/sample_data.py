from sqlalchemy import Table, Column, Integer, String, Float, MetaData

metadata = MetaData()

students = Table(
    "students",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String),
    Column("marks", Integer),
)

employees = Table(
    "employees",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String),
    Column("department", String),
    Column("salary", Integer),
)


def insert_sample_data(engine):
    metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(students.insert(), [
            {"name": "Amit", "marks": 85},
            {"name": "Neha", "marks": 92},
            {"name": "Rahul", "marks": 70},
            {"name": "Priya", "marks": 88},
            {"name": "Vikram", "marks": 65},
        ])
        conn.execute(employees.insert(), [
            {"name": "Ravi", "department": "IT", "salary": 60000},
            {"name": "Anita", "department": "HR", "salary": 50000},
            {"name": "Suresh", "department": "IT", "salary": 72000},
            {"name": "Kavita", "department": "Finance", "salary": 55000},
        ])
