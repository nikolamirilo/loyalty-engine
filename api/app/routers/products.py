from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.program import get_program
from app.models import Product, Program
from app.schemas import ProductCreate, ProductOut, ProductUpdate
from app.services.products import get_product_or_404

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    product = Product(**body.model_dump(), program_id=program.id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=list[ProductOut])
def list_products(
    # Aliased so the wire-level query key is camelCase like every other JSON
    # key in the API; the Python parameter stays snake_case.
    active_only: bool = Query(False, alias="activeOnly"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    q = db.query(Product).filter(Product.program_id == program.id)
    if active_only:
        q = q.filter(Product.is_active)
    return q.order_by(Product.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    return get_product_or_404(db, product_id, program)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: UUID,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    product = get_product_or_404(db, product_id, program)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    program: Program = Depends(get_program),
):
    product = get_product_or_404(db, product_id, program)
    db.delete(product)
    db.commit()
