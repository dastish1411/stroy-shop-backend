from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.order import SubOrder, SubOrderStatus
from app.models.payment import Payment, PaymentStatus, SupplierTransaction, TransactionType
from app.models.supplier import Supplier
from app.schemas.payment import PaymentCreate


def pay_sub_order(db: Session, sub_order_id: int, payment_data: PaymentCreate, user_id: int) -> Payment:
    sub_order = db.query(SubOrder).filter(SubOrder.id == sub_order_id).first()

    if not sub_order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if sub_order.order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Это не ваш заказ")

    if sub_order.status != SubOrderStatus.pending_payment:
        raise HTTPException(status_code=400, detail=f"Заказ уже в статусе '{sub_order.status.value}', оплата невозможна")

    for item in sub_order.items:
        if item.product.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Товар '{item.product.name}' закончился или его недостаточно на складе",
            )

    try:
        for item in sub_order.items:
            item.product.quantity -= item.quantity

        supplier = db.query(Supplier).filter(Supplier.id == sub_order.supplier_id).first()
        supplier.balance += sub_order.amount

        transaction = SupplierTransaction(
            supplier_id=supplier.id,
            sub_order_id=sub_order.id,
            amount=sub_order.amount,
            type=TransactionType.sale,
            balance_after=supplier.balance,
        )
        db.add(transaction)

        payment = Payment(
            sub_order_id=sub_order.id,
            user_id=user_id,
            amount=sub_order.amount,
            method=payment_data.method,
            status=PaymentStatus.success,
        )
        db.add(payment)

        sub_order.status = SubOrderStatus.paid

        db.commit()
        db.refresh(payment)

    except Exception:
        db.rollback()
        raise

    return payment


def get_payments_by_user(db: Session, user_id: int) -> list[Payment]:
    return db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc()).all()


def get_transactions_by_supplier(db: Session, supplier_id: int) -> list[SupplierTransaction]:
    return db.query(SupplierTransaction).filter(
        SupplierTransaction.supplier_id == supplier_id
    ).order_by(SupplierTransaction.created_at.desc()).all()


def get_sales_by_supplier(db: Session):
    results = (
        db.query(
            Supplier.id,
            Supplier.name,
            func.coalesce(func.sum(SupplierTransaction.amount), 0).label("total_sales"),
        )
        .outerjoin(SupplierTransaction, SupplierTransaction.supplier_id == Supplier.id)
        .filter(
            (SupplierTransaction.type == TransactionType.sale)
            | (SupplierTransaction.type.is_(None))
        )
        .group_by(Supplier.id, Supplier.name)
        .all()
    )

    return [
        {"supplier_id": r.id, "supplier_name": r.name, "total_sales": float(r.total_sales)}
        for r in results
    ]

def get_monthly_sales_by_supplier(db: Session):
    # group by месяц (обрезаем дату до месяца) и поставщик
    results = (
        db.query(
            func.date_trunc("month", SupplierTransaction.created_at).label("month"),
            Supplier.id.label("supplier_id"),
            Supplier.name.label("supplier_name"),
            func.sum(SupplierTransaction.amount).label("total"),
        )
        .join(Supplier, Supplier.id == SupplierTransaction.supplier_id)
        .filter(SupplierTransaction.type == TransactionType.sale)
        .group_by("month", Supplier.id, Supplier.name)
        .order_by("month")
        .all()
    )

    return [
        {
            "month": r.month.strftime("%Y-%m"),
            "supplier_id": r.supplier_id,
            "supplier_name": r.supplier_name,
            "total": float(r.total),
        }
        for r in results
    ]