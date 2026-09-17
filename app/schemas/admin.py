from pydantic import BaseModel


class AdminSummaryOut(BaseModel):
    total_clients: int
    total_suppliers: int
    total_products: int
    total_orders: int
    total_revenue: float


class SupplierSalesOut(BaseModel):
    supplier_id: int
    supplier_name: str
    total_sales: float


class MonthlySalesOut(BaseModel):
    month: str
    supplier_id: int
    supplier_name: str
    total: float