# scripts/reset_db.py
from storage.db import engine
from storage.orm import Base

def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Базата е нулирана.")

if __name__ == "__main__":
    reset_db()
