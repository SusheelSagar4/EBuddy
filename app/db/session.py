from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

Base = declarative_base()

# Initialize SQLAlchemy Engine with connection timeout to prevent silent hangs
engine = create_engine(
    settings.effective_db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 3}  # Strict 3-second connection timeout
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
