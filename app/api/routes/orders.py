from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_supplier
from app.schemas.order import OrderCreate, OrderOut, SubOrderOut, SubOrderStatusUpdate
from app.crud.order import (
    create_order,
    get_orders_by_user,
    get_sub_orders_by_supplier,
    update_sub_order_status,
)
from app.models.user import User
from app.models.supplier import Supplier
from app.models.order import SubOrder, SubOrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderOut)
def checkout(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_order(db, order_data, user_id=current_user.id)


@router.get("/history", response_model=list[OrderOut])
def order_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_orders_by_user(db, current_user.id)


@router.patch("/{sub_order_id}/confirm-delivery", response_model=SubOrderOut)
def confirm_delivery(
    sub_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub_order = db.query(SubOrder).filter(SubOrder.id == sub_order_id).first()
    if not sub_order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if sub_order.order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Это не ваш заказ")

    if sub_order.status != SubOrderStatus.shipped:
        raise HTTPException(status_code=400, detail="Подтвердить получение можно только для отправленных заказов")

    return update_sub_order_status(db, sub_order, SubOrderStatus.delivered)


# ---------- ДЛЯ ПОСТАВЩИКА ----------

@router.get("/supplier/orders", response_model=list[SubOrderOut])
def my_supplier_orders(
    db: Session = Depends(get_db),
    current_supplier: Supplier = Depends(get_current_supplier),
):
    return get_sub_orders_by_supplier(db, current_supplier.id)


@router.patch("/supplier/orders/{sub_order_id}/status", response_model=SubOrderOut)
def change_order_status(
    sub_order_id: int,
    status_data: SubOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_supplier: Supplier = Depends(get_current_supplier),
):
    sub_order = db.query(SubOrder).filter(SubOrder.id == sub_order_id).first()
    if not sub_order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if sub_order.supplier_id != current_supplier.id:
        raise HTTPException(status_code=403, detail="Это не ваш заказ")

    # поставщик может переводить только по разрешённой цепочке статусов
    allowed_transitions = {
        SubOrderStatus.paid: SubOrderStatus.processing,
        SubOrderStatus.processing: SubOrderStatus.shipped,
    }

    if sub_order.status not in allowed_transitions or allowed_transitions[sub_order.status] != status_data.status:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя перевести заказ из статуса '{sub_order.status.value}' в '{status_data.status.value}'",
        )

    return update_sub_order_status(db, sub_order, status_data.status)