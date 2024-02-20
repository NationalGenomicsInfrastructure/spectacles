import dotenv
from fastapi import FastAPI

dotenv.load_dotenv()

from .routers import auth


app = FastAPI()

app.include_router(auth.router)


@app.get("/")
async def index():
    return "Hello World"
