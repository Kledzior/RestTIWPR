import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv() 

LOCAL_DB_ADDRESS = os.environ.get("LOCAL_DB_ADDRESS", "sqlite:///./sql_app.db")

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_CONN_STRING", LOCAL_DB_ADDRESS)

if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)




connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL.lower() else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True,

    pool_recycle=3600,
    pool_size=10, 
    max_overflow=20, 
    pool_timeout=30
)
print(f"{SQLALCHEMY_DATABASE_URL}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logging.exception('Error while yielding db')
        raise e
    finally:
        db.close()