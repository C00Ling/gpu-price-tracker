from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.sql import func
from storage.db import Base

class GPU(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String, index=True, nullable=False)
    source = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    mean_fps = Column(Float, default=0.0)
    # Добавяме дата на създаване за исторически справки
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<GPU(model='{self.model}', price={self.price}, source='{self.source}')>"