import math
from sqlalchemy.orm import Session, joinedload
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(
    db: Session,
    category_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
):
    query = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.supplier),
    )

    if category_id is not None:
        query = query.filter(Product.category_id == category_id)

    # считаем ОБЩЕЕ количество товаров, подходящих под фильтр -
    # ДО применения limit/offset, иначе посчитаем только текущую страницу
    total = query.count()

    # offset - сколько записей "пропустить" перед текущей страницей
    # например, page=2, page_size=20 -> offset=20 (пропускаем первые 20)
    offset = (page - 1) * page_size

    items = query.offset(offset).limit(page_size).all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.supplier))
        .filter(Product.id == product_id)
        .first()
    )


def get_products_by_supplier(db: Session, supplier_id: int) -> list[Product]:
    return (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.supplier))
        .filter(Product.supplier_id == supplier_id)
        .all()
    )


def create_product(db: Session, product_data: ProductCreate, supplier_id: int) -> Product:
    new_product = Product(
        name=product_data.name,
        category_id=product_data.category_id,
        supplier_id=supplier_id,
        price=product_data.price,
        quantity=product_data.quantity,
        unit=product_data.unit,
        description=product_data.description,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def update_product(db: Session, product: Product, product_data: ProductUpdate) -> Product:
    update_data = product_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product: Product) -> None:
    db.delete(product)
    db.commit()