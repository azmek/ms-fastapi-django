import pathlib
import os
import io
import uuid
from functools import lru_cache
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Request,
    File,
    UploadFile
    )
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseSettings
from PIL import Image

class Settings(BaseSettings):
    debug: bool = False
    echo_active: bool = False
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
DEBUG=settings.debug
BASE_DIR = pathlib.Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"

app = FastAPI()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
#REST API

@app.get("/", response_class=HTMLResponse) #http GET -> json
def home_view(request: Request, settings:Settings = Depends(get_settings)):
    #return json.dumps({"message": "Hello World"})
    print(request)
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/") #http POST method
def home_detail_view():
    return {"message": "Hello World"}

@app.post("/img-echo/", response_class=FileResponse) #http POST method
async def img_echo_view(file:UploadFile = File(...), settings:Settings = Depends(get_settings)):
    if not settings.echo_active:
        raise HTTPException(detail="Invalid endpoint", status_code=400)
    UPLOAD_DIR.mkdir(exist_ok=True)
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str) #consider using opencv
    except:
        raise HTTPException(detail="Invalid image", status_code=400)
    fname = pathlib.Path(file.filename)
    fext = fname.suffix
    dest = UPLOAD_DIR / f"{uuid.uuid4()}{fext}"
    img.save(dest)
    return dest