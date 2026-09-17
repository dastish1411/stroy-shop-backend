from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_admin
from app.schemas.admin import AdminSummaryOut, SupplierSalesOut, MonthlySalesOut
from app.crud.admin import get_admin_summary
from app.crud.payment import get_sales_by_supplier, get_monthly_sales_by_supplier

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/summary", response_model=AdminSummaryOut, dependencies=[Depends(get_current_admin)])
def summary(db: Session = Depends(get_db)):
    return get_admin_summary(db)


@router.get("/sales-by-supplier", response_model=list[SupplierSalesOut], dependencies=[Depends(get_current_admin)])
def sales_by_supplier(db: Session = Depends(get_db)):
    return get_sales_by_supplier(db)


@router.get("/monthly-sales", response_model=list[MonthlySalesOut], dependencies=[Depends(get_current_admin)])
def monthly_sales(db: Session = Depends(get_db)):
    return get_monthly_sales_by_supplier(db)