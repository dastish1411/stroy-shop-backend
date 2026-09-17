from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category import CategoryCreate

def get_categories(db: Session) -> list[Category]:
    return db.query(Category).all()

def get_category_by_id(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()

def create_category(db: Session, category_data: CategoryCreate) -> Category:
    new_category = Category(
        name=category_data.name,
        image_url=category_data.image_url,
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()