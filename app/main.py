from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, categories, products, orders, payments, supplier, admin

app = FastAPI(title="Stroy Shop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://frontend-dastan.toolforge.rest",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(supplier.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"message": "Stroy Shop API работает"}