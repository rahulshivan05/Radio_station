from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import aiohttp
import asyncio
import random

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Radio Browser API servers
RADIO_BROWSER_SERVERS = [
    "de1.api.radio-browser.info",
    "nl1.api.radio-browser.info",
    "at1.api.radio-browser.info"
]

# Define Models
class RadioStation(BaseModel):
    stationuuid: str
    name: str
    url: str
    url_resolved: Optional[str] = None
    homepage: Optional[str] = None
    favicon: Optional[str] = None
    tags: Optional[str] = None
    country: Optional[str] = None
    countrycode: Optional[str] = None
    state: Optional[str] = None
    language: Optional[str] = None
    languagecodes: Optional[str] = None
    votes: Optional[int] = 0
    lastchangetime: Optional[str] = None
    codec: Optional[str] = None
    bitrate: Optional[int] = 0
    hls: Optional[int] = 0
    lastcheckok: Optional[int] = 1
    lastchecktime: Optional[str] = None
    lastcheckoktime: Optional[str] = None
    lastlocalchecktime: Optional[str] = None
    clicktimestamp: Optional[str] = None
    clickcount: Optional[int] = 0
    clicktrend: Optional[int] = 0
    ssl_error: Optional[int] = 0
    geo_lat: Optional[float] = None
    geo_long: Optional[float] = None
    has_extended_info: Optional[bool] = False

class Country(BaseModel):
    name: str
    iso_3166_1: str
    stationcount: int

class Genre(BaseModel):
    name: str
    stationcount: int

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Helper function to get a random radio browser server
def get_random_server():
    return f"https://{random.choice(RADIO_BROWSER_SERVERS)}"

# Helper function to make HTTP requests to radio browser API
async def make_radio_browser_request(endpoint: str, params: dict = None):
    server_url = get_random_server()
    url = f"{server_url}{endpoint}"
    
    headers = {
        "User-Agent": "GlobalRadioApp/1.0"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise HTTPException(status_code=response.status, detail=f"Radio API error: {response.status}")
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Radio API timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Radio API error: {str(e)}")

# Radio Station Endpoints
@api_router.get("/radio/search", response_model=List[RadioStation])
async def search_stations(
    name: Optional[str] = Query(None, description="Search by station name"),
    country: Optional[str] = Query(None, description="Filter by country"),
    tag: Optional[str] = Query(None, description="Filter by genre/tag"),
    language: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Search for radio stations with various filters"""
    params = {
        "limit": limit,
        "offset": offset,
        "hidebroken": "true",
        "order": "clickcount",
        "reverse": "true"
    }
    
    if name:
        params["name"] = name
    if country:
        params["country"] = country
    if tag:
        params["tag"] = tag
    if language:
        params["language"] = language
    
    stations = await make_radio_browser_request("/json/stations/search", params)
    return [RadioStation(**station) for station in stations]

@api_router.get("/radio/popular", response_model=List[RadioStation])
async def get_popular_stations(limit: int = Query(50, ge=1, le=100)):
    """Get most popular radio stations"""
    params = {
        "limit": limit,
        "hidebroken": "true",
        "order": "clickcount",
        "reverse": "true"
    }
    
    stations = await make_radio_browser_request("/json/stations/search", params)
    return [RadioStation(**station) for station in stations]

@api_router.get("/radio/countries", response_model=List[Country])
async def get_countries():
    """Get list of available countries"""
    countries = await make_radio_browser_request("/json/countries")
    return [Country(**country) for country in countries if country.get('stationcount', 0) > 0]

@api_router.get("/radio/genres", response_model=List[Genre])
async def get_genres(limit: int = Query(50, ge=1, le=100)):
    """Get list of available genres/tags"""
    params = {
        "limit": limit,
        "order": "stationcount",
        "reverse": "true"
    }
    
    genres = await make_radio_browser_request("/json/tags", params)
    return [Genre(name=genre['name'], stationcount=genre['stationcount']) for genre in genres]

@api_router.post("/radio/click/{station_uuid}")
async def click_station(station_uuid: str):
    """Register a click for a station (helps with popularity tracking)"""
    try:
        await make_radio_browser_request(f"/json/url/{station_uuid}")
        return {"message": "Click registered successfully"}
    except Exception as e:
        # Don't fail if click registration fails
        return {"message": "Click registration failed", "error": str(e)}

@api_router.get("/radio/station/{station_uuid}", response_model=RadioStation)
async def get_station_details(station_uuid: str):
    """Get detailed information about a specific station"""
    stations = await make_radio_browser_request(f"/json/stations/byuuid/{station_uuid}")
    if not stations:
        raise HTTPException(status_code=404, detail="Station not found")
    
    return RadioStation(**stations[0])

# Original endpoints
@api_router.get("/")
async def root():
    return {"message": "Global Radio API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()