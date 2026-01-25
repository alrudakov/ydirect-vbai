import uvicorn
import os

if __name__ == "__main__":
    # Запускаем uvicorn. "app.main:app" означает, что будет запущен объект app из файла app/main.py
    # reload=True автоматически перезапускает сервер при изменении кода.
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True) 