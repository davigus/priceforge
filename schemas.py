from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date

class PriceCalcRequest(BaseModel):
    product_sku: str = Field(..., description="SKU del prodotto da prezzare")
    requested_qty: float = 1
    as_of: Optional[date] = None
    validate: bool = False

class PriceCalcDetail(BaseModel):
    line_no: int
    kind: str
    ref_id: UUID
    description: Optional[str] = None
    uom: Optional[str] = None
    quantity: float
    unit_cost: float
    extended_cost: float
    source: str

class PriceCalcResponse(BaseModel):
    run_id: UUID
    product_id: UUID
    requested_qty: float
    markup_pct: float
    total_material_cost: float
    total_operation_cost: float
    total_other_cost: float
    total_cost: float
    price: float
    currency: str
    validated: bool
    items: List[PriceCalcDetail]
