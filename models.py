from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    chunks = relationship("FileChunk", back_populates="file")

class FileChunk(Base):
    __tablename__ = "file_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    content = Column(Text, nullable=False)
    chunk_order = Column(Integer)
    file = relationship("File", back_populates="chunks")