from fastapi import FastAPI

# from config import config_values
from .routers import auth


app = FastAPI()

app.include_router(auth.router)


@app.get("/")
async def index():
    return "Hello World"
