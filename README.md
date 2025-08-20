# PriceForge - Pricing/BOM Microservice (FastAPI + Postgres)

## Quick start
```bash
docker compose up -d --build
# seed sample data inside the container:
docker compose exec priceforge bash -lc "python app/seed.py"
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Postgres: localhost:5432 (db=priceforge, user=pf_user, pwd=pf_password)
- pgAdmin: http://localhost:8080 (admin@example.com / admin)

## Calculate price

POST `/pricing/calculate`

```json
{
  "product_sku": "P001",
  "requested_qty": 10,
  "validate": true
}
```
