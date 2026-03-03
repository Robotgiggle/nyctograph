import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from .routers import homepage, view_stored, global_stats, misc, login_signup

# ===== CORE APP SETUP =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    # pre-startup handlers go here
    yield
    # post-shutdown handlers go here

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="correcthorsebatterystaple")

app.include_router(homepage.router)
app.include_router(view_stored.router)
app.include_router(global_stats.router)
app.include_router(misc.router)
app.include_router(login_signup.router)