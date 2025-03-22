from fastapi import FastAPI

from .login.router import router as login_router
from .middleware import JWTAuthMiddleware
from .users.router import router as users_router

app = FastAPI(title="Marketplace")
app.add_middleware(JWTAuthMiddleware)

app.include_router(users_router)
app.include_router(login_router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
