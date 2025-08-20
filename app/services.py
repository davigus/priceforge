from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import (
    Product, BOM, BOMComponent, Material, MaterialCost, Operation, OperationCost,
    ProductCostOverride, PricingSettings, PriceCalculationRun, PriceCalculationDetail
)

def _get_cost_from_list(session: Session, table, id_field, ref_id, as_of):
    stmt = (
        select(table.unit_cost)
        .where(getattr(table, id_field) == ref_id)
        .where(table.valid_from <= as_of)
        .where((table.valid_to == None) | (table.valid_to >= as_of))
        .order_by(table.valid_from.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()

def _get_product_override(session: Session, product_id, kind, ref_id, as_of):
    stmt = (
        select(ProductCostOverride.override_unit_cost)
        .where(ProductCostOverride.product_id == product_id)
        .where(ProductCostOverride.kind == kind)
        .where(ProductCostOverride.ref_id == ref_id)
        .where(ProductCostOverride.valid_from <= as_of)
        .where((ProductCostOverride.valid_to == None) | (ProductCostOverride.valid_to >= as_of))
        .order_by(ProductCostOverride.valid_from.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()

def _active_or_valid_bom(session: Session, product_id, as_of):
    active = session.execute(
        select(BOM).where(BOM.product_id == product_id, BOM.is_active == True).order_by(BOM.version.desc()).limit(1)
    ).scalar_one_or_none()
    if active:
        return active
    latest_valid = session.execute(
        select(BOM).where(
            BOM.product_id == product_id,
            BOM.valid_from <= as_of,
            (BOM.valid_to == None) | (BOM.valid_to >= as_of)
        ).order_by(BOM.version.desc()).limit(1)
    ).scalar_one_or_none()
    return latest_valid

def _expand_product(session: Session, product_id, qty, as_of, snapshot_items, line_no_start=1):
    # Recursively expand a product's BOM.
    bom = _active_or_valid_bom(session, product_id, as_of)
    if not bom:
        raise ValueError(f"Nessuna BOM attiva/valida per product_id={product_id}")

    total_mat = 0.0
    total_op = 0.0
    cur_line = line_no_start

    for comp in sorted(bom.components, key=lambda c: c.line_no):
        qty_per_unit = float(comp.quantity) * (1.0 + float(comp.waste_pct or 0)/100.0)
        eff_qty = qty * qty_per_unit

        if comp.kind == "product":
            cur_line, sub_mat, sub_op = _expand_product(session, comp.ref_id, eff_qty, as_of, snapshot_items, cur_line)
            total_mat += sub_mat
            total_op += sub_op
            continue

        unit_cost = None
        source = None
        if comp.override_unit_cost is not None:
            unit_cost = float(comp.override_unit_cost)
            source = "override_bom"
        else:
            po = _get_product_override(session, bom.product_id, comp.kind, comp.ref_id, as_of)
            if po is not None:
                unit_cost = float(po)
                source = "override_product"
            else:
                if comp.kind == "material":
                    c = _get_cost_from_list(session, MaterialCost, "material_id", comp.ref_id, as_of)
                elif comp.kind == "operation":
                    c = _get_cost_from_list(session, OperationCost, "operation_id", comp.ref_id, as_of)
                else:
                    raise ValueError(f"Kind non supportato: {comp.kind}")
                if c is None:
                    raise ValueError(f"Nessun costo valido per {comp.kind} {comp.ref_id} alla data {as_of}")
                unit_cost = float(c)
                source = "listino"

        extended = eff_qty * unit_cost

        desc, uom = None, None
        if comp.kind == "material":
            m = session.get(Material, comp.ref_id)
            if m: desc, uom = m.name, m.uom
            total_mat += extended
        elif comp.kind == "operation":
            o = session.get(Operation, comp.ref_id)
            if o: desc, uom = o.name, o.uom
            total_op += extended

        snapshot_items.append({
            "line_no": cur_line,
            "kind": comp.kind,
            "ref_id": str(comp.ref_id),
            "description": desc,
            "uom": uom,
            "quantity": eff_qty,
            "unit_cost": unit_cost,
            "extended_cost": extended,
            "source": source
        })
        cur_line += 1

    return cur_line, total_mat, total_op

def calculate_and_persist(session: Session, product_sku: str, requested_qty: float = 1.0, as_of=None, validate=False):
    as_of = as_of or date.today()

    product = session.execute(select(Product).where(Product.sku == product_sku)).scalar_one_or_none()
    if not product:
        raise ValueError(f"Prodotto con SKU='{product_sku}' non trovato")

    settings = session.get(PricingSettings, True)
    default_markup = float(settings.default_markup_pct) if settings else 15.0
    markup_pct = float(product.default_markup_pct) if product.default_markup_pct is not None else default_markup
    currency = product.currency or (settings.currency if settings else "EUR")

    items = []
    _, tot_mat, tot_op = _expand_product(session, product.product_id, float(requested_qty), as_of, items, 1)
    tot_oth = 0.0
    tot = tot_mat + tot_op + tot_oth
    price = round(tot * (1 + markup_pct/100.0), 4)

    run = PriceCalculationRun(
        product_id=product.product_id,
        bom_id=_active_or_valid_bom(session, product.product_id, as_of).bom_id,
        requested_qty=requested_qty,
        markup_pct=markup_pct,
        total_material_cost=tot_mat,
        total_operation_cost=tot_op,
        total_other_cost=tot_oth,
        total_cost=tot,
        price=price,
        currency=currency,
        validated=validate,
        snapshot_json={
            "as_of": as_of.isoformat(),
            "requested_qty": requested_qty,
            "markup_pct": markup_pct,
            "currency": currency,
            "items": items
        }
    )
    session.add(run); session.flush()

    for it in items:
        det = PriceCalculationDetail(
            run_id=run.run_id,
            line_no=it["line_no"],
            kind=it["kind"],
            ref_id=it["ref_id"],
            description=it.get("description"),
            uom=it.get("uom"),
            quantity=it["quantity"],
            unit_cost=it["unit_cost"],
            extended_cost=it["extended_cost"],
            source=it["source"]
        )
        session.add(det)
    session.commit()
    return run, items
