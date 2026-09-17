from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_supplier
from app.schemas.payment import PaymentCreate, PaymentOut, SupplierFinanceOut
from app.crud.payment import pay_sub_order, get_payments_by_user, get_transactions_by_supplier
from app.models.user import User
from app.models.supplier import Supplier

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/{sub_order_id}", response_model=PaymentOut)
def pay(
    sub_order_id: int,
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return pay_sub_order(db, sub_order_id, payment_data, user_id=current_user.id)


@router.get("/history", response_model=list[PaymentOut])
def payment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_payments_by_user(db, current_user.id)


@router.get("/supplier/finance", response_model=SupplierFinanceOut)
def supplier_finance(
    db: Session = Depends(get_db),
    current_supplier: Supplier = Depends(get_current_supplier),
):
    transactions = get_transactions_by_supplier(db, current_supplier.id)
    return SupplierFinanceOut(
        balance=current_supplier.balance,
        transactions=transactions,
    )