from fastapi import FastAPI, Path
from typing import Optional
from pydantic import BaseModel,BaseConfig
import databases
import sqlalchemy
from sqlalchemy.dialects.postgresql import JSON

BaseConfig.arbitrary_types_allowed = True  # change #1

database_url = "postgresql://rsxmhaipetxgsy:6c3eca151f1bf454f58b6a833f9b96b6766365baa97868b9964d8adf60fc6281@ec2-54-91-223-99.compute-1.amazonaws.com:5432/d69ei6qdr31e4i"
database = databases.Database(database_url)
metadata = sqlalchemy.MetaData()

airports = sqlalchemy.Table(
    "airports",
    metadata,
    sqlalchemy.Column("id",sqlalchemy.String, primary_key = True),
    sqlalchemy.Column("name",sqlalchemy.String),
    sqlalchemy.Column("country",sqlalchemy.String),
    sqlalchemy.Column("city",sqlalchemy.String),
    sqlalchemy.Column("position",sqlalchemy.JSON),
)

flights = sqlalchemy.Table(
    "flights",
    metadata,
    sqlalchemy.Column("id",sqlalchemy.String, primary_key = True),
    sqlalchemy.Column("departure",sqlalchemy.String),
    sqlalchemy.Column("destination",sqlalchemy.String),
)

engine = sqlalchemy.create_engine(
    database_url
)
metadata.create_all(engine)

app = FastAPI()

class Airport(BaseModel):
    id: str
    name: str
    country: str
    city: str
    position: JSON

class Flight(BaseModel):
    id: str
    departure: str
    destination: str

@app.get("/")
def index():
    return {"name": "First Data"}

# @app.get("/get-airports/")
# async def get_airports():
#     query = "SELECT * FROM airports"
#     return await database.fetch_all(query = query)

# @app.get("/get-airport/{airport_id}")
# def get_airport(airport_id):
#     return students[student_id]

# @app.get("/get-by-name/{student_id}")
# def get_student(*, student_id: int, name: Optional[str] = None, test : int):
#     for student_id in students:
#         if students[student_id]["name"] == name:
#             return students[student_id]
#     return {"Data": "Not found"}

# @app.post("/create-student/{student_id}")
# def create_student(student_id : int, student : Student):
#     if student_id in students:
#         return {"Error": "Student exists"}

#     students[student_id] = student
#     return students[student_id]

# @app.put("/update-student/{student_id}")
# def update_student(student_id: int, student: UpdateStudent):
#     if student_id not in students:
#         return {"Error": "Student does not exist"}

#     if student.name != None:
#         students[student_id].name = student.name

#     if student.age != None:
#         students[student_id].age = student.age

#     if student.year != None:
#         students[student_id].year = student.year

#     return students[student_id]

# @app.delete("/delete-student/{student_id}")
# def delete_student(student_id: int):
#     if student_id not in students:
#         return {"Error": "Student does not exist"}

#     del students[student_id]
#     return {"Message": " Student deleted successfully"}