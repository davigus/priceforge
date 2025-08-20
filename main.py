from fastapi import FastAPI
from .database import Base, engine
from .routers import products, pricing
import time
from sqlalchemy.exc import OperationalError

app = FastAPI(title="PriceForge - Pricing Service")

# Tentativo di creare le tabelle con retry (DB potrebbe non essere pronto)
def init_db_with_retry(retries=15, delay=2):
    for i in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as e:
            if i == retries - 1:
                raise
            time.sleep(delay)

@app.on_event("startup")
def on_startup():
    init_db_with_retry()

app.include_router(products.router)
app.include_router(pricing.router)

@app.get("/")
def root():
    return {"message": "PriceForge API up & running"}