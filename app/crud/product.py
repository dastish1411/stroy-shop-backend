from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get_products(db: Session, category_id: int | None = None) -> list[Product]:
    query = db.query(Product)
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    return query.all()


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def get_products_by_supplier(db: Session, supplier_id: int) -> list[Product]:
    return db.query(Product).filter(Product.supplier_id == supplier_id).all()


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