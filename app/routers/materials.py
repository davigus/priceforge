from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..database import get_db
from ..models import Material
from pydantic import BaseModel
from typing import List
from uuid import UUID

router = APIRouter(prefix="/materials", tags=["materials"])

class MaterialIn(BaseModel):
    material_id: str
    code: str
    name: str
    uom: str | None = None

class MaterialOut(MaterialIn):
    Material_id: UUID
    class Config:
        from_attributes = True

@router.post("/", response_model=MaterialOut)
def create_material(body: MaterialIn, db: Session = Depends(get_db)):
    p = Material(**body.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p

@router.get("/", response_model=List[MaterialOut])
def list_materials(db: Session = Depends(get_db)):
    return db.query(Material).all()

@router.get("/by-name/{name}", response_model=MaterialOut)
def get_material_by_name(name, db: Session = Depends(get_db)):
    stmt = select(Material).where(func.lower(Material.name) == name.lower())
    Material = db.execute(stmt).scalars().first()
    if not Material:
        raise HTTPException(status_code=404, detail="Material not found")
    return Material

@router.get("/by-code/{code}", response_model=MaterialOut)
def get_material_by_code(code, db: Session = Depends(get_db)):
    stmt = select(Material).where(func.lower(Material.code) == code.lower())
    material = db.execute(stmt).scalars().first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material