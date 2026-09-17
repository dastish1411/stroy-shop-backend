from pydantic import BaseModel


class SupplierMeOut(BaseModel):
    id: int
    name: str
    description: str | None
    contact_phone: str | None
    balance: float

    class Config:
        from_attributes = True