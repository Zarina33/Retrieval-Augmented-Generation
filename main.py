from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from . import models, database

app = FastAPI()

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                
                <!-- Форма загрузки файла -->
                <div class="card mb-4">
                    <div class="card-body">
                        <h5 class="card-title">Upload File</h5>
                        <div class="mb-3">
                            <input type="file" class="form-control" id="fileInput">
                            <button onclick="uploadFile()" class="btn btn-primary mt-2">Upload</button>
                        </div>
                    </div>
                </div>

                <!-- Секция для вопросов -->
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Ask Question</h5>
                        <div class="mb-3">
                            <select class="form-select mb-3" id="fileSelect">
                                <option selected>Choose file...</option>
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
                    const file = fileInput.files[0];
                    if (!file) {
                        alert('Please select a file');
                        return;
                    }

                    const formData = new FormData();
                    formData.append('file', file);

                    try {
                        const response = await fetch('/upload', {
                            method: 'POST',
                            body: formData
                        });
                        const result = await response.json();
                        alert('File uploaded successfully');
                        loadFiles();  // Обновляем список файлов
                    } catch (error) {
                        alert('Error uploading file');
                    }
                }

                // Загрузка списка файлов
                async function loadFiles() {
                    const response = await fetch('/files');
                    const files = await response.json();
                    const select = document.getElementById('fileSelect');
                    select.innerHTML = '<option selected>Choose file...</option>';
                    files.forEach(file => {
                        const option = document.createElement('option');
                        option.value = file.id;
                        option.textContent = file.filename;
                        select.appendChild(option);
                    });
                }

                // Задать вопрос
                async function askQuestion() {
                    const fileId = document.getElementById('fileSelect').value;
                    const question = document.getElementById('questionInput').value;

                    if (fileId === 'Choose file...' || !question) {
                        alert('Please select a file and enter a question');
                        return;
                    }

                    try {
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
                        document.getElementById('answer').innerHTML = `
                            <div class="alert alert-info">
                                ${result.response}
                            </div>
                        `;
                    } catch (error) {
                        alert('Error getting answer');
                    }
                }

                // Загружаем список файлов при загрузке страницы
                loadFiles();
            </script>
        </body>
    </html>
    """