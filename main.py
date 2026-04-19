from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

# # Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["https://console.waveify.ai"],  # Your frontend domain
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "OPTIONS"],  # Include OPTIONS
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def debug_cors(request, call_next):
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    response = await call_next(request)
    print(f"Response headers: {dict(response.headers)}")
    return response


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
    db = SessionLocal()
    try:
        # Get total customers
        total_customers = db.query(CustomerDB).count()
        
        # Get customers grouped by date
        from sqlalchemy import func, extract
        customers_by_date = db.query(
            func.date(CustomerDB.created_at).label('date'),
            func.count(CustomerDB.id).label('count')
        ).group_by(func.date(CustomerDB.created_at)).all()
        
        # Convert to dictionary format
        daily_counts = {str(row.date): row.count for row in customers_by_date}
        
        # Generate HTML table
        html_table = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Customer Dashboard</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .stats {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 30px;
                }}
                .stat-box {{
                    background-color: #007bff;
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    flex: 1;
                    margin: 0 10px;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                }}
                .stat-label {{
                    font-size: 0.9em;
                    opacity: 0.9;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f8f9fa;
                    font-weight: bold;
                    color: #495057;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .no-data {{
                    text-align: center;
                    color: #666;
                    font-style: italic;
                    padding: 40px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Customer Dashboard</h1>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">{total_customers}</div>
                        <div class="stat-label">Total Customers</div>
                    </div>
                </div>
                
                <h2>Daily Subscriptions</h2>
                {generate_date_table(daily_counts)}
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_table)
    finally:
        db.close()

def generate_date_table(daily_counts):
    if not daily_counts:
        return '<div class="no-data">No customer data available</div>'
    
    # Sort dates in descending order
    sorted_dates = sorted(daily_counts.keys(), reverse=True)
    
    table_rows = ""
    for date in sorted_dates:
        table_rows += f"""
        <tr>
            <td>{date}</td>
            <td>{daily_counts[date]}</td>
        </tr>
        """
    
    return f"""
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>New Customers</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    """

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
