from fastapi import FastAPI
from app.routes import payments, refunds
from app.database import Base, engine
from app.routes import webhooks

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(payments.router)
app.include_router(refunds.router)
app.include_router(webhooks.router)