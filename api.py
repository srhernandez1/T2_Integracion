from fastapi import FastAPI, Path, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional,List,Union
from pydantic import BaseModel,BaseConfig
import databases
import sqlalchemy
import requests
import json

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
    sqlalchemy.Column("departure",sqlalchemy.JSON),
    sqlalchemy.Column("destination",sqlalchemy.JSON),
    sqlalchemy.Column("total_distance",sqlalchemy.Float),
    sqlalchemy.Column("traveled_distance",sqlalchemy.Float),
    sqlalchemy.Column("bearing",sqlalchemy.Float),
    sqlalchemy.Column("position",sqlalchemy.JSON),
)

engine = sqlalchemy.create_engine(
    database_url
)
metadata.create_all(engine)

app = FastAPI()

class Airport(BaseModel):
    id: Union[str,None] = None
    name: Union[str,None] = None
    country: Union[str,None] = None
    city: Union[str,None] = None
    position: Union[dict,None] = None

class Flight_inp(BaseModel):
    id: str
    departure: str
    destination: str

class Flight(BaseModel):
    id: str
    departure: dict
    destination: dict
    total_distance: float
    traveled_distance: float
    bearing: float
    position: dict

@app.on_event("startup")
async def startup():
    await database.connect()
@app.on_event("shutdown")
async def startup():
    await database.disconnect()

@app.get("/")
async def index():
    return {"Bienvenido":"T2"}
@app.get("/status",status_code = 204)
async def get_status():
    return {"name": "204"}
@app.delete("/data")
async def delete_db():
    conn = engine.connect()
    stmt = airports.delete()
    conn.execute(stmt)
    stmt_2 = flights.delete()
    conn.execute(stmt_2)
    return

#Manejar errores y hacer las weas q faltan.
@app.get("/airports",response_model = List[Airport])
async def get_airports():
    query = airports.select()
    return await database.fetch_all(query)
@app.get("/flights",response_model = List[Flight])
async def get_flights():
    query = flights.select()
    return await database.fetch_all(query)
@app.get("/airports/{airport_id}",response_model = Airport)
async def get_airports(airport_id):
    query = sqlalchemy.select(airports).where(airports.c.id == airport_id)
    query_err = sqlalchemy.select(airports).where(airports.c.id == airport_id)
    err = await database.fetch_one(query_err)
    if err ==None:
        return JSONResponse(
            status_code=400,
            content="Ta malo",
        )
    return await database.fetch_one(query)
@app.get("/flights/{flight_id}",response_model = Flight)
async def get_airports(flight_id):
    query = sqlalchemy.select(flights).where(flights.c.id == flight_id)
    query_err = sqlalchemy.select(flights).where(flights.c.id == flight_id)
    err = await database.fetch_one(query_err)
    if err ==None:
        raise HTTPException(status_code=404, detail="Flight with id "+str(flight_id)+" not found")
    return await database.fetch_one(query)


@app.post("/airports",response_model = Airport,status_code = 201)
async def create_airports(airport: Airport):
    for field in airport.__fields__:
        if getattr(airport,field) == None:
            return JSONResponse(
            status_code=400,
            content={"error":"Missing field "+field}
        )
    query_err = sqlalchemy.select(airports).where(airports.c.id == airport.id)
    err = await database.fetch_one(query_err)
    if err !=None and err.id == airport.id:
        return JSONResponse(
            status_code=409,
            content={"error":"Airport with id "+str(err.id)+" already exists"}
        )
    query = airports.insert().values(id = airport.id,name = airport.name,country = airport.country,city = airport.city, position = airport.position)
    last_id = await database.execute(query)
    return Airport(id = airport.id,name = airport.name,country = airport.country,city = airport.city, position = airport.position)
@app.post("/flights",response_model = Flight,status_code = 201)
async def create_flight(flight: Flight_inp):
    query_dep = sqlalchemy.select(airports).where(airports.c.id == flight.departure)
    dep = await database.fetch_one(query_dep)
    query_des = sqlalchemy.select(airports).where(airports.c.id == flight.destination)
    des = await database.fetch_one(query_des)
    dic_dep=json.loads(dep.position)
    dic_des=json.loads(des.position)
    link = "https://tarea-2.2022-2.tallerdeintegracion.cl/distance?initial={0},{1}&final={2},{3}".format(dic_dep["lat"],dic_dep["long"],dic_des["lat"],dic_des["long"])
    response = requests.get(link)
    dic = response.json()
    
    query = flights.insert().values(id = flight.id,departure = {"id":dep.id,"name":dep.name},
    destination = {"id":des.id,"name":des.name},total_distance = dic["distance"],traveled_distance = 0,bearing = 0,
    position = {"lat":dic_dep["lat"],"long":dic_dep["long"]})

    last_id = await database.execute(query)
    return Flight(id = flight.id,departure = {"id":dep.id,"name":dep.name},
    destination = {"id":des.id,"name":des.name},total_distance = dic["distance"],traveled_distance = 0,bearing = 0,
    position = {"lat":dic_dep["lat"],"long":dic_dep["long"]})

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