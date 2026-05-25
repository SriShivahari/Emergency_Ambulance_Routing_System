import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    GOOGLE_MAPS_API_KEY ="AIzaSyALr0rte2iS7R0NObUQXDFqtChVHC4DOYA"
