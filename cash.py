# backend/app/main.py
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from app.models import File
from app.database import SessionLocal, engine, Base
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from . import models, database
import base64
app = FastAPI()

# Создаем таблицы
models.Base.metadata.create_all(bind=engine)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Query(BaseModel):
    file_id: int
    query_text: str

app = FastAPI()

# Инициализация модели
model = Llama(
    model_path="path/to/your/mistral-7b-v0.1.Q4_K_M.gguf",  # Укажите путь к вашей модели
    n_ctx=2048,
    n_threads=6
)

@app.post("/query")
async def ask_question(query: Query, db: Session = Depends(get_db)):
    try:
        # Получаем файл из БД
        file = db.query(models.File).filter(models.File.id == query.file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Декодируем содержимое файла
        content = base64.b64decode(file.content).decode('utf-8', errors='ignore')

        # Формируем промпт
        prompt = f"""На основе следующего контекста ответьте на вопрос.

Контекст:
{content}

Вопрос: {query.query_text}

Ответ:"""

        # Генерируем ответ
        response = model.create_completion(
            prompt,
            max_tokens=512,
            temperature=0.7,
            top_p=0.9,
            stop=["Вопрос:", "\n\n"]
        )

        return {"response": response['choices'][0]['text'].strip()}

    except Exception as e:
        print(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Читаем содержимое файла как бинарные данные
        content = await file.read()
        # Конвертируем в base64 для хранения
        content_base64 = base64.b64encode(content).decode('utf-8')

        # Создаем запись в БД
        db_file = models.File(
            filename=file.filename,
            content=content_base64,  # Сохраняем как base64
            file_type=file.content_type
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return {"message": "File uploaded successfully", "id": db_file.id}
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def get_files(db: Session = Depends(get_db)):
    try:
        files = db.query(models.File).all()
        return [{"id": file.id, "filename": file.filename} for file in files]
    except Exception as e:
        print(f"Error fetching files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file/{file_id}")
async def get_file_content(file_id: int, db: Session = Depends(get_db)):
    try:
        file = db.query(models.File).filter(models.File.id == file_id).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Декодируем content из base64
        content = base64.b64decode(file.content)
        
        return {
            "id": file.id,
            "filename": file.filename,
            "content": content.decode('utf-8', errors='ignore')
        }
    except Exception as e:
        print(f"Error getting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>RAG System</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>RAG System</h1>
                
                <!-- Загрузка файла -->
                <div class="card mb-4">
                    <div class="card-body">
                        <h5 class="card-title">Upload File</h5>
                        <div class="mb-3">
                            <input type="file" class="form-control" id="fileInput">
                            <button onclick="uploadFile()" class="btn btn-primary mt-2">Upload</button>
                        </div>
                        <div id="uploadStatus"></div>
                    </div>
                </div>

                <!-- Секция для вопросов -->
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Ask Question</h5>
                        <div class="mb-3">
                            <select class="form-select mb-3" id="fileSelect">
                                <option value="">Select a file...</option>
                            </select>
                            <input type="text" class="form-control mb-2" id="questionInput" placeholder="Enter your question">
                            <button onclick="askQuestion()" class="btn btn-primary">Ask</button>
                        </div>
                        <div id="answer" class="mt-3"></div>
                    </div>
                </div>
            </div>

            <script>
                // Загрузка файла
                async function uploadFile() {
                    const fileInput = document.getElementById('fileInput');
                    const statusDiv = document.getElementById('uploadStatus');
                    const file = fileInput.files[0];
                    
                    if (!file) {
                        alert('Please select a file');
                        return;
                    }

                    const formData = new FormData();
                    formData.append('file', file);

                    try {
                        statusDiv.innerHTML = 'Uploading...';
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();
                        statusDiv.innerHTML = 'File uploaded successfully!';
                        fileInput.value = ''; // Очищаем input
                        await loadFiles();  // Обновляем список файлов
                    } catch (error) {
                        statusDiv.innerHTML = 'Error uploading file: ' + error.message;
                    }
                }

                // Загрузка списка файлов
                async function loadFiles() {
                    try {
                        const response = await fetch('/files');
                        const files = await response.json();
                        const select = document.getElementById('fileSelect');
                        
                        // Очищаем текущий список
                        select.innerHTML = '<option value="">Select a file...</option>';
                        
                        // Добавляем файлы в список
                        if (files && files.length > 0) {
                            files.forEach(file => {
                                const option = document.createElement('option');
                                option.value = file.id;
                                option.textContent = file.filename;
                                select.appendChild(option);
                            });
                        }
                    } catch (error) {
                        console.error('Error loading files:', error);
                    }
                }

                // Задать вопрос
                async function askQuestion() {
                    const fileSelect = document.getElementById('fileSelect');
                    const fileId = fileSelect.value;
                    const question = document.getElementById('questionInput').value;
                    const answerDiv = document.getElementById('answer');

                    if (!fileId) {
                        alert('Please select a file');
                        return;
                    }

                    if (!question.trim()) {
                        alert('Please enter a question');
                        return;
                    }

                    try {
                        answerDiv.innerHTML = 'Getting answer...';
                        const response = await fetch('/query', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                file_id: parseInt(fileId),
                                query_text: question
                            })
                        });
                        const result = await response.json();
                        answerDiv.innerHTML = `
                            <div class="alert alert-info">
                                <strong>Answer:</strong><br>
                                ${result.response}
                            </div>
                        `;
                    } catch (error) {
                        answerDiv.innerHTML = `
                            <div class="alert alert-danger">
                                Error getting answer: ${error.message}
                            </div>
                        `;
                    }
                }

                // Загружаем список файлов при загрузке страницы
                document.addEventListener('DOMContentLoaded', function() {
                    loadFiles();
                });
            </script>
        </body>
    </html>
    """