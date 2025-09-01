from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..database import get_db
from ..models import Operation
from pydantic import BaseModel
from typing import List
from uuid import UUID

router = APIRouter(prefix="/operationss", tags=["operations"])

class OperationIn(BaseModel):
    operation_id: str
    code: str
    name: str
    uom: str | None = None

class OperationOut(OperationIn):
    Material_id: UUID
    class Config:
        from_attributes = True

@router.post("/", response_model=OperationOut)
def create_operation(body: OperationIn, db: Session = Depends(get_db)):
    p = Operation(**body.model_dump())
    db.add(p); db.commit(); db.refresh(p)
    return p

@router.get("/", response_model=List[OperationOut])
def list_operations(db: Session = Depends(get_db)):
    return db.query(Operation).all()

@router.get("/by-name/{name}", response_model=OperationOut)
def get_operation_by_name(name, db: Session = Depends(get_db)):
    stmt = select(Operation).where(func.lower(Operation.name) == name.lower())
    Operation = db.execute(stmt).scalars().first()
    if not Operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    return Operation

@router.get("/by-code/{code}", response_model=OperationOut)
def get_operation_by_code(code, db: Session = Depends(get_db)):
    stmt = select(Operation).where(func.lower(Operation.code) == code.lower())
    operation = db.execute(stmt).scalars().first()
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    return operation