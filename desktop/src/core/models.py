from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(255))
    source = Column(String(255))
    status = Column(String(50), nullable=False)
    last_contact = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Lead(id={self.id}, name='{self.name}', status='{self.status}')>"

class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    address = Column(String(255), nullable=False)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    property_type = Column(String(50))
    bedrooms = Column(Integer)
    bathrooms = Column(Numeric(3,1))
    square_feet = Column(Integer)
    lot_size = Column(Integer)
    year_built = Column(Integer)
    listing_price = Column(Numeric(15,2))
    listing_status = Column(String(50))
    mls_id = Column(String(100))
    owner_id = Column(Integer) # Placeholder for future relationship
    agent_id = Column(Integer) # Placeholder for future relationship
    date_added = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Property(id={self.id}, address='{self.address}', status='{self.listing_status}')>"

class Campaign(Base):
    __tablename__ = 'campaigns'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    start_date = Column(Date)
    date_created = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', status='{self.status}')>"

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(Date)
    status = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False)
    assigned_to = Column(String(255))
    lead_id = Column(Integer) # Placeholder for future relationship
    property_id = Column(Integer) # Placeholder for future relationship
    date_created = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
