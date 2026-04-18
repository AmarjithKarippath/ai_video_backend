# FastAPI Customer Subscription Application

A FastAPI application for collecting and managing customer email subscriptions with SQLite database.

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Start the FastAPI server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. The API will be available at `http://localhost:8000`

## API Endpoints

### Root
- **GET** `/` - Welcome message

### Customer Management
- **GET** `/customers/` - Get all subscribed customers
- **POST** `/customers/subscribe` - Subscribe a new customer (name and email)

### Health Check
- **GET** `/health` - Check application health

## API Documentation

Once the server is running, you can access:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Example Usage

### Customer Subscription
```bash
# Subscribe a new customer
curl -X POST "http://localhost:8000/customers/subscribe" \
     -H "Content-Type: application/json" \
     -d '{"name": "John Doe", "email": "john@example.com"}'

# Get all customers
curl "http://localhost:8000/customers/"
```

## Features

- FastAPI with automatic API documentation
- Pydantic models for data validation
- SQLite database for customer data persistence
- Email uniqueness validation for customer subscriptions
- Proper HTTP status codes and error handling
- Health check endpoint
- CORS support (can be added as needed)
