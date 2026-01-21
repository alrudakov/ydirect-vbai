"""
Скрипт для получения OAuth токена Yandex
"""
import requests
import webbrowser
from urllib.parse import urlencode
from config import CLIENT_ID, CLIENT_SECRET, OAUTH_URL, TOKEN_URL


def get_auth_url():
    """Генерирует URL для авторизации"""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        # Важно: scope должен запрашиваться в authorize URL, иначе токен может быть без прав.
        "scope": "direct:api",
        # Чтобы Яндекс всегда показывал экран подтверждения прав (удобно при отладке).
        "force_confirm": "yes",
    }
    return f"{OAUTH_URL}?{urlencode(params)}"


def get_token(code: str) -> dict:
    """Обменивает код авторизации на токен"""
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    
    response = requests.post(TOKEN_URL, data=data)
    return response.json()


def main():
    # Шаг 1: Получить URL для авторизации
    auth_url = get_auth_url()
    print("=" * 60)
    print("Шаг 1: Перейди по ссылке и авторизуйся:")
    print(auth_url)
    print("=" * 60)
    
    # Открыть в браузере
    open_browser = input("\nОткрыть в браузере? (y/n): ")
    if open_browser.lower() == 'y':
        webbrowser.open(auth_url)
    
    # Шаг 2: Ввести код
    print("\nШаг 2: После авторизации скопируй код из URL или со страницы")
    code = input("Введи код: ").strip()
    
    if not code:
        print("Код не введен!")
        return
    
    # Шаг 3: Получить токен
    print("\nПолучаю токен...")
    result = get_token(code)
    
    if "access_token" in result:
        print("\n" + "=" * 60)
        print("УСПЕХ! Твой access_token:")
        print(result["access_token"])
        print("=" * 60)
        print(f"\nRefresh token: {result.get('refresh_token', 'N/A')}")
        print(f"Expires in: {result.get('expires_in', 'N/A')} секунд")
        
        # Сохранить токен
        with open("token.txt", "w") as f:
            f.write(result["access_token"])
        print("\nТокен сохранен в token.txt")
    else:
        print("\nОшибка получения токена:")
        print(result)


if __name__ == "__main__":
    main()

