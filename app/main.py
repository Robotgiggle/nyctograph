import asyncio
from os.path import dirname
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from .routers import homepage, login, my_dreams, signup, global_stats, misc
from .utils import flash
from .stat_calc import global_stat_calc_loop

# ===== CORE APP SETUP =====

COOKIE_SECRET_KEY = "correcthorsebatterystaple"

@asynccontextmanager
async def lifespan(app: FastAPI):
    calcLoopTask = asyncio.create_task(global_stat_calc_loop(2)) # in production, this number should be *much* higher
    yield # pre-startup handlers go before this, post-shutdown handlers go after
    #calcLoopTask.cancel()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory=dirname(__file__)+"/static"), name="static")

app.add_middleware(SessionMiddleware, secret_key=COOKIE_SECRET_KEY)

app.include_router(homepage.router)
app.include_router(my_dreams.router)
app.include_router(global_stats.router)
app.include_router(login.router)
app.include_router(signup.router)
app.include_router(misc.router)

@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    for error in exc.errors():
        flash(request, f"Validation error for '{error['loc'][-1]}': {error['msg']}", "warn")
    return RedirectResponse(request['path'], status_code=303)