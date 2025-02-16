from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database
from typing import List
import shutil
import os

app = FastAPI()

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем директорию для загруженных файлов
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "RAG System API"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Сохраняем файл
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Сохраняем информацию о файле в БД
        db_file = models.File(
            filename=file.filename,
            file_type=file.content_type
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return {
            "id": db_file.id,
            "filename": db_file.filename,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files", response_model=List[dict])
async def get_files(db: Session = Depends(get_db)):
    try:
        files = db.query(models.File).all()
        return [
            {
                "id": file.id,
                "filename": file.filename,
                "file_type": file.file_type,
                "upload_date": file.upload_date
            }
            for file in files
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file/{file_id}")
async def get_file(file_id: int, db: Session = Depends(get_db)):
    try:
        file = db.query(models.File).filter(models.File.id == file_id).first()
        if file is None:
            raise HTTPException(status_code=404, detail="File not found")
        return {
            "id": file.id,
            "filename": file.filename,
            "file_type": file.file_type,
            "upload_date": file.upload_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))