from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_supplier
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut, PaginatedProductsOut
from app.crud.product import (
    get_products,
    get_product_by_id,
    get_products_by_supplier,
    create_product,
    update_product,
    delete_product,
)
from app.models.supplier import Supplier

router = APIRouter(tags=["products"])


# ---------- ПУБЛИЧНЫЙ КАТАЛОГ (доступен всем, без авторизации) ----------

@router.get("/products", response_model=PaginatedProductsOut)
def list_products(
    category_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    return get_products(db, category_id, page, page_size)

@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return product


# ---------- ЛИЧНЫЙ КАБИНЕТ ПОСТАВЩИКА (доступно только supplier) ----------

@router.get("/supplier/products", response_model=list[ProductOut])
def list_my_products(
    db: Session = Depends(get_db),
    current_supplier: Supplier = Depends(get_current_supplier),
):
    return get_products_by_supplier(db, current_supplier.id)


@router.post("/supplier/products", response_model=ProductOut)
def add_my_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_supplier: Supplier = Depends(get_current_supplier),
):
    return create_product(db, product_data, supplier_id=current_supplier.id)


@router.patch("/supplier/products/{product_id}", response_model=ProductOut)
def edit_my_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_supplier: Supplier = Depends(get_current_supplier),
):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    if product.supplier_id != current_supplier.id:
        raise HTTPException(status_code=403, detail="Вы можете редактировать только свои товары")

    return update_product(db, product, product_data)


@router.delete("/supplier/products/{product_id}")
def remove_my_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_supplier: Supplier = Depends(get_current_supplier),
):
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")

    if product.supplier_id != current_supplier.id:
        raise HTTPException(status_code=403, detail="Вы можете удалять только свои товары")

    delete_product(db, product)
    return {"message": "Товар удалён"}