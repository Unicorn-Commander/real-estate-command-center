# scripts/init_db.py
import asyncio
from sqlalchemy import create_engine, text

async def initialize_database():
    # Connect to PostgreSQL
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/postgres")
    
    # Create database if not exists
    with engine.connect() as conn:
        conn.execute(text("COMMIT"))
        try:
            conn.execute(text("CREATE DATABASE realestate_db"))
        except:
            pass  # Database already exists
    
    # Connect to new database
    engine = create_engine("postgresql://realestate:commander123@localhost:5432/realestate_db")
    
    # Create tables
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS properties (
            id SERIAL PRIMARY KEY,
            address TEXT NOT NULL,
            mls_number VARCHAR(50),
            bedrooms INTEGER,
            bathrooms NUMERIC(3,1),
            sqft INTEGER,
            year_built INTEGER,
            property_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cmas (
            id SERIAL PRIMARY KEY,
            property_id INTEGER REFERENCES properties(id),
            report_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pdf_path TEXT
        );
        """))
        
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS leads (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone VARCHAR(20),
            email TEXT,
            source VARCHAR(50),
            status VARCHAR(20) DEFAULT 'new',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contact TIMESTAMP
        );
        """))
        
        # Add more tables as needed
        conn.execute(text("COMMIT"))

if __name__ == "__main__":
    asyncio.run(initialize_database())