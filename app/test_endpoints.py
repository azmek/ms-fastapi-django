import shutil
import time
import io
from fastapi.testclient import TestClient
from app.main import app, BASE_DIR, UPLOAD_DIR,get_settings
from PIL import Image, ImageChops

client = TestClient(app) # r=requests

def test_get_home():
    response = client.get("/") # requests.get("") # python requests
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_invalid_file_upload_error():
    response = client.post("/") # requests.get("") # python requests
    assert response.status_code == 422
    assert "application/json" in response.headers["content-type"]

def test_prediction_upload_missing_headers():
    img_saved_path = BASE_DIR / "images"
    settings=get_settings()
    #path = BASE_DIR / "static" / "img" / "test.jpg"
    for path in img_saved_path.glob("*"):
        try:
            img = Image.open(path)
        except:
            img = None
        response = client.post("/",
                               files={"file":open(path, 'rb')}
                               ) # requests.get("") # python requests
        assert response.status_code == 401


def test_prediction_upload():
    img_saved_path = BASE_DIR / "images"
    settings=get_settings()
    #path = BASE_DIR / "static" / "img" / "test.jpg"
    for path in img_saved_path.glob("*"):
        try:
            img = Image.open(path)
        except:
            img = None
        response = client.post("/",
                               files={"file":open(path, 'rb')},
                               headers = {"Authorization": f"JWT {settings.app_auth_token}"}
                               ) # requests.get("") # python requests
        if img is None:
            assert response.status_code == 400
        else:
            #returning a valid image
            assert response.status_code == 200
            data = response.json()
            assert len(data.keys()) == 2


def test_echo_upload():
    img_saved_path = BASE_DIR / "images"
    #path = BASE_DIR / "static" / "img" / "test.jpg"
    for path in img_saved_path.glob("*"):
        try:
            img = Image.open(path)
        except:
            img = None
        response = client.post("/img-echo/", files={"file":open(path, 'rb')}) # requests.get("") # python requests
        if img is None:
            assert response.status_code == 400
        else:
            #returning a valid image
            assert response.status_code == 200
            r_stream = io.BytesIO(response.content)
            echo_img = Image.open(r_stream)
            difference = ImageChops.difference(img, echo_img).getbbox()
            assert difference is None
    #time.sleep(3)
    shutil.rmtree(UPLOAD_DIR)