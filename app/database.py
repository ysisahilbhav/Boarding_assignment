import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
from dotenv import load_dotenv
import redis


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"

database = Database(DATABASE_URL)
metadata = MetaData()

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

if USE_REDIS:
    redis_client = redis.Redis(host='redis', port=6379, db=0)
else:
    redis_client = None