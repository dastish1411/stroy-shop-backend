from pydantic import BaseModel


# что нужно прислать, чтобы создать категорию
class CategoryCreate(BaseModel):
    name: str
    image_url: str

# что мы отдаём в ответ
class CategoryOut(BaseModel):
    id: int
    name: str
    image_url:str

    class Config:
        from_attributes = True