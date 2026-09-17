from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.category import CategoryCreate, CategoryOut
from app.crud.category import get_categories, get_category_by_id, create_category, delete_category
from app.models.user import User, UserRole
from app.models.product import Product

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return get_categories(db)


@router.post("/", response_model=CategoryOut)
def add_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Только администратор может создавать категории")

    return create_category(db, category_data)


@router.delete("/{category_id}")
def remove_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Только администратор может удалять категории")

    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    # проверяем, что у категории нет товаров - иначе удаление сломает их
    products_count = db.query(Product).filter(Product.category_id == category_id).count()
    if products_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить категорию: в ней есть {products_count} товар(ов)",
        )

    delete_category(db, category)
    return {"message": "Категория удалена"}