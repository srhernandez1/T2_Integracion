from unittest import result
from fastapi import FastAPI, Path
from typing import Optional,List
from pydantic import BaseModel,BaseConfig
import databases
import sqlalchemy

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
    position: dict

class Flight(BaseModel):
    id: str
    departure: str
    destination: str

@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def startup():
    await database.disconnect()

@app.get("/")
def index():
    return {"name": "First Data"}

@app.get("/airports/",response_model = List[Airport])
async def get_airports():
    query = airports.select()
    return await database.fetch_all(query)

@app.get("/airports/{airport_id}",response_model = Airport)
async def get_airports(airport_id):
    query = sqlalchemy.select(airports).where(airports.c.id == airport_id)
    res = await database.fetch_one(query)
    return Airport(id = res.id,name = res.name,country = res.country,city = res.city, position = res.position)

@app.post("/airports/",response_model = Airport)
async def create_airports(airport: Airport):
    query = airports.insert().values(id = airport.id,name = airport.name,country = airport.country,city = airport.city, position = airport.position)
    last_id = await database.execute(query)
    return Airport(id = airport.id,name = airport.name,country = airport.country,city = airport.city, position = airport.position)

@app.post("/flights/",response_model = Flight)
async def create_flight(flight: Flight):
    query = flights.insert().values(id = flight.id,departure = flight.departure, destination = flight.destination)
    last_id = await database.execute(query)
    return Flight(id = flight.id,departure = flight.departure, destination = flight.destination)

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