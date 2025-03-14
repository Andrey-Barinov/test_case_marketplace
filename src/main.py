from fastapi import FastAPI

app = FastAPI(title="Marketplace")


@app.get("/")
def read_root():
    return {"Hello": "World"}
