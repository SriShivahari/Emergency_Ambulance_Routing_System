import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    GOOGLE_MAPS_API_KEY ="AIzaSyClb_D1rCjzMb_IzH0P5BDruWG7YzdLRJ0"
