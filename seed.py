from datetime import date
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import (Product, Material, MaterialCost, Operation, OperationCost, BOM, BOMComponent, PricingSettings)

Base.metadata.create_all(bind=engine)
db: Session = SessionLocal()

# Settings
if not db.get(PricingSettings, True):
    db.add(PricingSettings(settings_id=True, default_markup_pct=20.0, currency="EUR"))
    db.commit()

# Product
p = Product(sku="P001", name="Tavolo da cucina", default_markup_pct=20.0)
db.add(p); db.commit(); db.refresh(p)

# Materials
m = Material(code="M001", name="Legno massello", uom="m2")
db.add(m); db.commit(); db.refresh(m)
db.add(MaterialCost(material_id=m.material_id, unit_cost=30.0, currency="EUR", valid_from=date(2024,1,1)))
db.commit()

# Operations
o = Operation(code="O001", name="Taglio legno", uom="h")
db.add(o); db.commit(); db.refresh(o)
db.add(OperationCost(operation_id=o.operation_id, unit_cost=25.0, currency="EUR", valid_from=date(2024,1,1)))
db.commit()

# BOM (active)
b = BOM(product_id=p.product_id, version=1, is_active=True, valid_from=date(2024,1,1))
db.add(b); db.commit(); db.refresh(b)

db.add(BOMComponent(bom_id=b.bom_id, line_no=1, kind="material", ref_id=m.material_id, quantity=5))
db.add(BOMComponent(bom_id=b.bom_id, line_no=2, kind="operation", ref_id=o.operation_id, quantity=2))
db.commit()

print("Seed data inserted. Product SKU=P001")
db.close()
