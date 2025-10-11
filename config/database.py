from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import Generator, Optional, Dict, Any
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = os.getenv("DATABASE_URL") or f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
	DATABASE_URL,
	echo=True,
	pool_pre_ping=True,
	pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator:
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()

def test_connection() -> Dict[str, Any]:
	try:
		with engine.connect() as conn:
			row = conn.execute(text("SELECT 1")).fetchone()
			ok = bool(row and row[0] == 1)
			return {"status": "success" if ok else "error", "message": "DB OK" if ok else "DB test failed"}
	except Exception as e:
		return {"status": "error", "message": f"Connection failed: {str(e)}"}

def get_database_info() -> Dict[str, Any]:
	try:
		with engine.connect() as conn:
			version = conn.execute(text("SELECT version()")).fetchone()[0]
			dbname = conn.execute(text("SELECT current_database()")).fetchone()[0]
			masked_url = DATABASE_URL.replace(DB_PASSWORD or "", "***") if DB_PASSWORD else DATABASE_URL
			return {"database_name": dbname, "postgresql_version": version, "connection_url": masked_url}
	except Exception as e:
		return {"error": f"Failed to get database info: {str(e)}"}