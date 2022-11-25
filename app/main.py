import pathlib
import os
import io
import uuid
from functools import lru_cache
from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Depends,
    Request,
    File,
    UploadFile
    )
import pytesseract
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseSettings
from PIL import Image

class Settings(BaseSettings):
    app_auth_token: str
    debug: bool = False
    echo_active: bool = False
    app_auth_token_prod: str = None
    skip_auth: bool = False

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

    return templates.TemplateResponse("home.html", {"request": request})

def verify_auth(authorization = Header(None), settings:Settings = Depends(get_settings)):
    """
    Authorization: Bearer <token>
    {"Authorization": "Bearer <token>"}
    """
    if settings.debug and settings.skip_auth:
        return
    if authorization is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    label, token = authorization.split()
    if token != settings.app_auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.post("/") #http POST method
async def prediction_view(file:UploadFile = File(...),authorization = Header(None),  settings:Settings = Depends(get_settings)):
    verify_auth(authorization, settings)
    bytes_str = io.BytesIO(await file.read())
    try:
        img = Image.open(bytes_str) #consider using opencv
    except:
        raise HTTPException(detail="Invalid image", status_code=400)
    preds = pytesseract.image_to_string(img)
    predictions = [x for x in preds.split("\n")]
    return {"results": predictions, "original":preds}


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