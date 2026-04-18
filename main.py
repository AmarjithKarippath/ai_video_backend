from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Database setup
DATABASE_URL = "sqlite:///./customers.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class CustomerDB(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="FastAPI Customer Management App",
    description="A FastAPI application for customer subscription management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Customer(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    created_at: Optional[datetime] = None

class CustomerCreate(BaseModel):
    name: str
    email: str

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Customer Management App"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# GET all customers
@app.get("/customers/", response_model=List[Customer])
async def get_all_customers():
    db = SessionLocal()
    try:
        customers = db.query(CustomerDB).all()
        return customers
    finally:
        db.close()

# POST subscribe new customer
@app.post("/customers/subscribe", response_model=Customer, status_code=201)
async def subscribe_customer(customer: CustomerCreate):
    db = SessionLocal()
    try:
        # Check if email already exists
        existing_customer = db.query(CustomerDB).filter(CustomerDB.email == customer.email).first()
        if existing_customer:
            raise HTTPException(status_code=400, detail="Email already subscribed")
        
        # Create new customer
        db_customer = CustomerDB(name=customer.name, email=customer.email)
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        return db_customer
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
