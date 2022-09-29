from fastapi import FastAPI, status,Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from typing import Optional,List,Union,Any
from pydantic import BaseModel,BaseConfig
import databases
import sqlalchemy
import requests
import json

BaseConfig.arbitrary_types_allowed = True  # change #1

database_url = "postgresql://wkgvjaocsllfnd:c334971c4fe42edcbd5f83f9cf7f9dd1f802c135787caf4aa13a3258386bfa77@ec2-54-91-223-99.compute-1.amazonaws.com:5432/d9ba30nouerlcg"
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
class Patch_In(BaseModel):
    name: str

class Patch_Fl(BaseModel):
    lat: float
    long: float

class Airport(BaseModel):
    id: Optional[str]
    name: Optional[str]
    country: Optional[str]
    city: Optional[str]
    position: Optional[dict]

class Flight_inp(BaseModel):
    id: Union[str,None] = None
    departure: Union[str,None] = None
    destination: Union[str,None] = None

class Flight(BaseModel):
    id: str
    departure: dict
    destination: dict
    total_distance: float
    traveled_distance: float
    bearing: float
    position: dict

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"error": exc.errors()})
    )

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
            status_code=404,
            content=jsonable_encoder({"error":"Airport with id "+str(airport_id)+" not found"}),
        )
    return await database.fetch_one(query)
@app.get("/flights/{flight_id}",response_model = Flight)
async def get_airports(flight_id):
    query = sqlalchemy.select(flights).where(flights.c.id == flight_id)
    query_err = sqlalchemy.select(flights).where(flights.c.id == flight_id)
    err = await database.fetch_one(query_err)
    if err == None:
        return JSONResponse(
            status_code=404,
            content=jsonable_encoder({"error":"Flight with id "+str(flight_id)+" not found"}),
        )
    return await database.fetch_one(query)

 
@app.post("/airports",response_model = Airport,status_code = 201)
async def create_airports(airport: Airport):
    for field in airport.__fields__:
        if getattr(airport,field) == None:
            return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error":"Missing parameter "+field}),
        )
    check_pos = airport.position
    if not check_pos:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error":"Invalid type of field position, got <class 'list'> expecting <class 'dict'>"}),
        )
    if not (-90<=check_pos["lat"]<=90):
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": "lat must be between -90 and 90"}),
        )
    if not (-180<=check_pos["long"]<=180):
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error": "long must be between -180 and 180"}),
        )
    query_err = sqlalchemy.select(airports).where(airports.c.id == airport.id)
    err = await database.fetch_one(query_err)
    if err !=None and err.id == airport.id:
        return JSONResponse(
            status_code=409,
            content=jsonable_encoder({"error":"Airport with id "+str(err.id)+" already exists"}),
        )
    query = airports.insert().values(id = airport.id,name = airport.name,country = airport.country,city = airport.city, position = airport.position)
    last_id = await database.execute(query)
    return Airport(id = airport.id,name = airport.name,country = airport.country,city = airport.city, position = airport.position)

@app.post("/flights",response_model = Flight,status_code = 201)
async def create_flight(flight: Flight_inp):
    if flight.departure == flight.destination:
        return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error":"departure and destination airports cannot be equal"}),
        )
    for field in flight.__fields__:
        if getattr(flight,field) == None:
            return JSONResponse(
            status_code=400,
            content=jsonable_encoder({"error":"Missing field "+field}),
        )
    query_err = sqlalchemy.select(flights).where(flights.c.id == flight.id)
    err = await database.fetch_one(query_err)
    if err !=None and err.id == flight.id:
        return JSONResponse(
            status_code=409,
            content=jsonable_encoder({"error":"Flight with id "+str(err.id)+" already exists"}),
        )
    query_dep = sqlalchemy.select(airports).where(airports.c.id == flight.departure)
    dep = await database.fetch_one(query_dep)
    query_des = sqlalchemy.select(airports).where(airports.c.id == flight.destination)
    des = await database.fetch_one(query_des)
    if dep == None:
        return JSONResponse(
            status_code=404,
            content=jsonable_encoder({"error":"Airport with id "+str(flight.departure)+" does not exist"}),
        )
    if des == None:
        return JSONResponse(
            status_code=404,
            content=jsonable_encoder({"error":"Airport with id "+str(flight.destination)+" does not exist"}),
        )
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

@app.patch("/airports/{airport_id}")
async def edit_airport(airport_id,nombre:Patch_In):
    query_err = sqlalchemy.select(airports).where(airports.c.id == airport_id)
    err = await database.fetch_one(query_err)
    if err ==None:
        return JSONResponse(
            status_code=404,
            content=jsonable_encoder({"error":"Airport with id "+str(airport_id)+" not found"}),
        )
    conn = engine.connect()
    stmt = airports.update().values(name = nombre.name).where(airports.c.id == airport_id)
    corr = conn.execute(stmt)
    return JSONResponse(
            status_code=204,
        )

@app.patch("/flights/{flight_id}")
async def edit_airport(flight_id,coord:Patch_Fl):
    query_err = sqlalchemy.select(flights).where(flights.c.id == flight_id)
    err = await database.fetch_one(query_err)
    if err ==None:
        return JSONResponse(
            status_code=404,
            content=jsonable_encoder({"error":"Flight with id "+str(flight_id)+" not found"}),
        )
    conn = engine.connect()
    stmt = flights.update().values(position = {"lat":coord.lat,"long":coord.long}).where(flights.c.id == flight_id)
    corr = conn.execute(stmt)
    return JSONResponse(
            status_code=204,
        )