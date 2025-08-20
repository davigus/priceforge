import uuid
from sqlalchemy import Column, String, Text, Boolean, Date, Numeric, ForeignKey, Integer, CheckConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

class Product(Base):
    __tablename__ = "products"
    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(64), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    currency = Column(String(3), nullable=False, default="EUR")
    default_markup_pct = Column(Numeric(6,3))
    is_sellable = Column(Boolean, nullable=False, default=True)
    boms = relationship("BOM", back_populates="product", cascade="all, delete-orphan")

class Material(Base):
    __tablename__ = "materials"
    material_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    uom = Column(String(16), nullable=False)

class MaterialCost(Base):
    __tablename__ = "material_costs"
    material_cost_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_id = Column(UUID(as_uuid=True), ForeignKey("materials.material_id", ondelete="CASCADE"), nullable=False)
    unit_cost = Column(Numeric(12,4), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date)

class Operation(Base):
    __tablename__ = "operations"
    operation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(64), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    uom = Column(String(16), nullable=False)

class OperationCost(Base):
    __tablename__ = "operation_costs"
    operation_cost_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id = Column(UUID(as_uuid=True), ForeignKey("operations.operation_id", ondelete="CASCADE"), nullable=False)
    unit_cost = Column(Numeric(12,4), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date)

class BOM(Base):
    __tablename__ = "boms"
    bom_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date)
    product = relationship("Product", back_populates="boms")
    components = relationship("BOMComponent", back_populates="bom", cascade="all, delete-orphan")
    __table_args__ = (CheckConstraint("version >= 1", name="chk_bom_version"),)

class BOMComponent(Base):
    __tablename__ = "bom_components"
    bom_component_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bom_id = Column(UUID(as_uuid=True), ForeignKey("boms.bom_id", ondelete="CASCADE"), nullable=False)
    line_no = Column(Integer, nullable=False)
    kind = Column(String(20), nullable=False)  # 'material' | 'operation' | 'product'
    ref_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Numeric(14,6), nullable=False, default=1)
    waste_pct = Column(Numeric(6,3), nullable=False, default=0)
    override_unit_cost = Column(Numeric(12,4))
    bom = relationship("BOM", back_populates="components")

class ProductCostOverride(Base):
    __tablename__ = "product_cost_overrides"
    product_cost_override_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(20), nullable=False)  # material | operation
    ref_id = Column(UUID(as_uuid=True), nullable=False)
    override_unit_cost = Column(Numeric(12,4), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date)

class PricingSettings(Base):
    __tablename__ = "pricing_settings"
    settings_id = Column(Boolean, primary_key=True, default=True)
    default_markup_pct = Column(Numeric(6,3), nullable=False, default=15.000)
    currency = Column(String(3), nullable=False, default="EUR")

class PriceCalculationRun(Base):
    __tablename__ = "price_calculation_runs"
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    bom_id = Column(UUID(as_uuid=True), ForeignKey("boms.bom_id", ondelete="SET NULL"))
    requested_qty = Column(Numeric(14,6), nullable=False, default=1)
    markup_pct = Column(Numeric(6,3), nullable=False)
    total_material_cost = Column(Numeric(14,4), nullable=False)
    total_operation_cost = Column(Numeric(14,4), nullable=False)
    total_other_cost = Column(Numeric(14,4), nullable=False, default=0)
    total_cost = Column(Numeric(14,4), nullable=False)
    price = Column(Numeric(14,4), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    validated = Column(Boolean, nullable=False, default=False)
    snapshot_json = Column(JSON, nullable=False)

class PriceCalculationDetail(Base):
    __tablename__ = "price_calculation_details"
    detail_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("price_calculation_runs.run_id", ondelete="CASCADE"), nullable=False)
    line_no = Column(Integer, nullable=False)
    kind = Column(String(20), nullable=False)
    ref_id = Column(UUID(as_uuid=True), nullable=False)
    description = Column(String(200))
    uom = Column(String(16))
    quantity = Column(Numeric(20,8), nullable=False)
    unit_cost = Column(Numeric(12,4), nullable=False)
    extended_cost = Column(Numeric(14,4), nullable=False)
    source = Column(String(32), nullable=False)
