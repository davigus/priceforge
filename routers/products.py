from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product
from pydantic import BaseModel
from typing import List
from uuid import UUID

router = APIRouter(prefix="/products", tags=["products"])

class ProductIn(BaseModel):
    sku: str
    name: str
    description: str | None = None
    currency: str = "EUR"
    default_markup_pct: float | None = None
    is_sellable: bool = True

class ProductOut(ProductIn):
    product_id: UUID
    class Config:
        from_attributes = True

@router.post("/", response_model=ProductOut)
def create_product(body: ProductIn, db: Session = Depends(get_db)):
    p = Product(**body.dict())
    db.add(p); db.commit(); db.refresh(p)
    return p

@router.get("/", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
