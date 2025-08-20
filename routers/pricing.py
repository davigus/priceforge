from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import PriceCalcRequest, PriceCalcResponse, PriceCalcDetail
from ..services import calculate_and_persist

router = APIRouter(prefix="/pricing", tags=["pricing"])

@router.post("/calculate", response_model=PriceCalcResponse)
def calculate_price(req: PriceCalcRequest, db: Session = Depends(get_db)):
    try:
        run, items = calculate_and_persist(
            session=db,
            product_sku=req.product_sku,
            requested_qty=req.requested_qty,
            as_of=req.as_of,
            validate=req.validate
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PriceCalcResponse(
        run_id=run.run_id,
        product_id=run.product_id,
        requested_qty=float(run.requested_qty),
        markup_pct=float(run.markup_pct),
        total_material_cost=float(run.total_material_cost),
        total_operation_cost=float(run.total_operation_cost),
        total_other_cost=float(run.total_other_cost),
        total_cost=float(run.total_cost),
        price=float(run.price),
        currency=run.currency,
        validated=run.validated,
        items=[PriceCalcDetail(**it) for it in items]
    )
