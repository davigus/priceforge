from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
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
    p = Product(**body.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p

@router.get("/", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@router.get("/by-name/{name}", response_model=ProductOut)
def get_product_by_name(name, db: Session = Depends(get_db)):
    stmt = select(Product).where(func.lower(Product.name) == name.lower())
    product = db.execute(stmt).scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/by-sku/{sku}", response_model=ProductOut)
def get_product_by_name(sku, db: Session = Depends(get_db)):
    stmt = select(Product).where(func.lower(Product.sku) == sku.lower())
    product = db.execute(stmt).scalars().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product