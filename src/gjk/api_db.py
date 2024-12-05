import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from gjk.config import Settings

# Load settings from environment or .env file
settings = Settings(_env_file=dotenv.find_dotenv())

# Create the SQLAlchemy engine
# You can customize pool_size, max_overflow, and pool_timeout if needed
engine = create_engine(
    settings.db_url.get_secret_value(),
    echo=False,  # Set to True for verbose SQL logging (debugging)
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Overflow beyond the pool size
    pool_timeout=30,  # Timeout in seconds for acquiring a connection
)

# Create the session factory (SessionLocal is a common convention)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,  # Prevent auto-commit of transactions
    autoflush=False,  # Prevent auto-flush of transactions
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
