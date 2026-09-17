from fastapi import APIRouter, Depends
from app.api.deps import get_current_supplier
from app.schemas.supplier import SupplierMeOut
from app.models.supplier import Supplier

router = APIRouter(prefix="/supplier", tags=["supplier"])


@router.get("/me", response_model=SupplierMeOut)
def get_my_supplier_profile(current_supplier: Supplier = Depends(get_current_supplier)):
    return current_supplier