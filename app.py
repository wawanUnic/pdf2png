from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pdf2image import convert_from_bytes
from PIL import Image, ImageFile
import os
import uuid

ImageFile.LOAD_TRUNCATED_IMAGES = True

app = FastAPI()

STATIC_DIR = "static"
TEMP_DIR = "temp_files"
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def form():
    return """
    <html>
    <head>
        <title>PDF ➜ PNG</title>
        <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
        <style>
            body { font-family: sans-serif; text-align: center; padding: 40px; }
            #dropzone {
                width: 400px; height: 150px;
                border: 2px dashed #999;
                border-radius: 10px;
                margin: 20px auto;
                line-height: 150px;
                color: #666; background-color: #f9f9f9;
            }
            #dropzone.dragover {
                background-color: #e0ffe0;
                border-color: #4caf50;
                color: #333;
            }
            #loader {
                display: none;
                color: green;
                font-weight: bold;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <h2>📄 Перетащите PDF или выберите вручную</h2>
        <div id="dropzone">Перетащите PDF сюда</div>

        <form id="uploadForm" action="/convert/" enctype="multipart/form-data" method="post">
            <input id="fileInput" name="file" type="file" accept="application/pdf" required><br><br>

            <label>DPI:</label>
            <select name="dpi">
                <option value="100">100</option>
                <option value="150" selected>150</option>
                <option value="200">200</option>
                <option value="300">300</option>
            </select><br><br>

            <label>Ширина PNG (px):</label>
            <select name="width">
                <option value="600">600</option>
                <option value="800">800</option>
                <option value="1000" selected>1000</option>
                <option value="1200">1200</option>
                <option value="1500">1500</option>
            </select><br><br>

            <label>Размер выходного файла:</label>
            <select name="quality">
                <option value="1">1 — максимальное качество</option>
                <option value="2">2</option>
                <option value="3" selected>3 — сбалансировано</option>
                <option value="4">4</option>
                <option value="5">5 — минимальный размер файла</option>
            </select><br><br>

            <input type="submit" value="Конвертировать">
        </form>

        <div id="loader">⏳ Обработка файла...</div>

        <script>
            const form = document.getElementById('uploadForm');
            const loader = document.getElementById('loader');
            const fileInput = document.getElementById('fileInput');
            const dropzone = document.getElementById('dropzone');

            dropzone.addEventListener("dragover", e => {
                e.preventDefault(); dropzone.classList.add("dragover");
            });
            dropzone.addEventListener("dragleave", () => {
                dropzone.classList.remove("dragover");
            });
            dropzone.addEventListener("drop", e => {
                e.preventDefault();
                dropzone.classList.remove("dragover");
                fileInput.files = e.dataTransfer.files;
            });
            form.addEventListener("submit", () => {
                loader.style.display = "block";
            });
        </script>
    </body>
    </html>
    """

@app.post("/convert/", response_class=HTMLResponse)
async def convert_pdf(
    file: UploadFile = File(...),
    dpi: int = Form(...),
    width: int = Form(...),
    quality: int = Form(...)
):
    if (
        dpi not in [100, 150, 200, 300]
        or width not in [600, 800, 1000, 1200, 1500]
        or quality not in [1, 2, 3, 4, 5]
    ):
        return HTMLResponse("Неверные параметры", status_code=400)

    contents = await file.read()
    pages = convert_from_bytes(contents, dpi=dpi)

    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS

    resized_pages = []
    heights = []

    for page in pages:
        scale = width / page.width
        height = int(page.height * scale)
        resized = page.resize((width, height), resample=resample)
        resized_pages.append(resized)
        heights.append(height)

    total_height = sum(heights)
    result = Image.new("RGB", (width, total_height), "white")

    y_offset = 0
    for img in resized_pages:
        result.paste(img, (0, y_offset))
        y_offset += img.height

    filename = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(TEMP_DIR, filename)
    result.save(output_path, format="PNG", compress_level=quality)

    return f"""
    <html>
    <head>
        <title>Готово</title>
        <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
    </head>
    <body style="text-align:center; font-family:sans-serif; padding: 60px;">
        <h2>✅ Конвертация завершена!</h2>
        <a href="/download/{filename}" download="converted.png">📥 Скачать PNG</a><br><br>
        <form action="/reset/" method="get">
            <button type="submit">🔁 Конвертировать ещё раз</button>
        </form>
    </body>
    </html>
    """

@app.get("/download/{filename}")
async def download_file(filename: str):
    path = os.path.join(TEMP_DIR, filename)
    return FileResponse(path, filename="converted.png", media_type="image/png")

@app.get("/reset/")
async def reset_and_reload():
    for f in os.listdir(TEMP_DIR):
        full = os.path.join(TEMP_DIR, f)
        if os.path.isfile(full):
            os.remove(full)
    return RedirectResponse(url="/", status_code=303)
