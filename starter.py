"""
Описание запроса создания кофе (POST):

- HTTP-метод и URL: POST https://pycourse-2026.duckdns.org/coffee/hot/
- Необходимые заголовки: Content-Type: application/json
- Параметры JSON-тела и тип каждого:
  - title (string): Название напитка. Обязательное.
  - description (string): Описание напитка. Обязательное.
  - ingredients (array of strings): Список ингредиентов. Обязательное.
  - image (string): URL изображения. Обязательное.
  - id (number): ID напитка. Необязательное.
- Ограничения на значения:
  - Ограничений на значения не было найдено
- Поля, задаваемые клиентом: title, description, ingredients, image, id.
- Поля, создаваемые сервером: id.
- Ожидаемый успешный статус: 201 Created.
- Форма ответа: JSON-объект, содержащий все переданные поля плюс сгенерированное поле id.
- Подтвержденные правила:
  - Запросами подтверждено, что сервер возвращает 201 и присваивает числовой id если он не был задан в запросе.
  - Клиент самостоятельно валидирует типы перед отправкой.
"""

from uuid import uuid4

import requests

JsonObject = dict[str, object]


class CoffeeApiError(Exception):
    pass


class CoffeeNotFoundError(CoffeeApiError):
    pass


class SampleApisCoffeeClient:
    def __init__(
        self,
        base_url: str = "https://pycourse-2026.duckdns.org/coffee/hot/",
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def list_drinks(self) -> list[JsonObject]:
        response = self._request("GET")
        return response.json()

    def get_drink(self, drink_id: int) -> JsonObject:
        response = self._request("GET", f"{drink_id}")
        return response.json()

    def create_drink(self, payload: JsonObject) -> JsonObject:
        if not isinstance(payload.get("ingredients"), list):
            raise TypeError("Поле 'ingredients' должно быть списком")
        if not payload.get("title") or not isinstance(payload.get("title"), str):
            raise ValueError("Поле 'title' должно быть непустой строкой")
        if not payload.get("description") or not isinstance(
            payload.get("description"), str
        ):
            raise ValueError("Поле 'description' должно быть непустой строкой")

        response = self._request("POST", "", payload)
        return response.json()

    def replace_drink(
        self,
        drink_id: int,
        payload: JsonObject,
    ) -> JsonObject:
        response = self._request("PUT", str(drink_id), payload)
        return response.json()

    def update_drink(
        self,
        drink_id: int,
        changes: JsonObject,
    ) -> JsonObject:
        response = self._request("PATCH", str(drink_id), changes)
        return response.json()

    def delete_drink(self, drink_id: int) -> None:
        self._request("DELETE", str(drink_id))

    def _request(
        self,
        method: str,
        path: str = "",
        payload: JsonObject | None = None,
    ) -> requests.Response:
        url = f"{self._base_url}/{path.lstrip('/')}" if path else self._base_url
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
        except requests.exceptions.Timeout:
            raise CoffeeApiError(
                f"Таймаут запроса {method} {url}, результат неизвестен проверьте вручную"
            )

        except requests.exceptions.RequestException as e:
            raise CoffeeApiError(f"Произошла ошибка при запросе {method} {url}: {e}")

        if response.status_code == 404:
            raise CoffeeNotFoundError(f"Такого напитка не найдено по {url}")

        if not response.ok:
            raise CoffeeApiError(
                f"Ошибка API ({response.status_code}): {response.text}"
            )

        if response.content:
            content_type = response.headers.get("Content-Type", "").lower()
            if "application/json" not in content_type:
                raise CoffeeApiError(
                    f"Ожидался JSON, получен Content-Type: {content_type}"
                )

        return response


def main() -> int:
    client = SampleApisCoffeeClient()
    marker = uuid4().hex[:8]
    created_id = None
    try:
        print("1. GET коллекции: получаем список горячих напитков.")
        drinks = client.list_drinks()
        print(f"   Успешно получено {len(drinks)} напитков.")

        print("2. POST: создаем новый напиток с уникальной меткой группы.")
        payload = {
            "title": f"Test Coffee {marker}",
            "description": "Тестовый напиток для проверки API",
            "ingredients": ["Вода", "Кофе"],
            "image": "https://example.com/test.jpg",
        }
        created_drink = client.create_drink(payload)
        created_id = created_drink["id"]
        print(f"   Напиток создан, получен id={created_id}")

        print("3. GET: получаем созданный напиток и сравниваем поля.")
        fetched = client.get_drink(created_id)
        if fetched.get("title") != payload["title"]:
            raise ValueError("Ошибка: title не совпадает с отправленным")
        if fetched.get("description") != payload["description"]:
            raise ValueError("Ошибка: description не совпадает с отправленным")
        if fetched.get("ingredients") != payload["ingredients"]:
            raise ValueError("Ошибка: ingredients не совпадает с отправленным")
        if fetched.get("image") != payload["image"]:
            raise ValueError("Ошибка: image не совпадает с отправленным")
        print("   Поля успешно совпадают с отправленными.")

        print("4. PUT: полностью заменяем данные напитка.")
        put_payload = {
            "title": f"Replaced Coffee {marker}",
            "description": "Полностью новое описание",
            "ingredients": ["Молоко", "Какао"],
            "image": "https://example.com/replaced.jpg",
        }
        client.replace_drink(created_id, put_payload)

        fetched_after_put = client.get_drink(created_id)
        if fetched_after_put.get("title") != put_payload["title"]:
            raise ValueError("Ошибка PUT: title не совпадает")
        if fetched_after_put.get("description") != put_payload["description"]:
            raise ValueError("Ошибка PUT: description не совпадает")
        if fetched_after_put.get("ingredients") != put_payload["ingredients"]:
            raise ValueError("Ошибка PUT: ingredients не совпадают")

        print("5. PATCH: изменяем часть данных (только описание).")
        patch_changes = {"description": "Изменено только описание через PATCH"}
        client.update_drink(created_id, patch_changes)

        print("   Повторный GET после PATCH: проверяем частичное изменение.")
        fetched_after_patch = client.get_drink(created_id)
        if fetched_after_patch.get("description") != patch_changes["description"]:
            raise ValueError("Ошибка PATCH: description не изменился")
        if fetched_after_patch.get("title") != put_payload["title"]:
            raise ValueError("Ошибка PATCH: title должен был сохраниться")
        if fetched_after_patch.get("ingredients") != put_payload["ingredients"]:
            raise ValueError("Ошибка PATCH: ingredients должны были сохраниться")
        print("   Поле изменено, остальные поля сохранились.")

        print("6. DELETE: удаляем созданный напиток.")
        client.delete_drink(created_id)

        print("7. GET: убеждаемся, что возвращается ожидаемый 404.")
        deleted_id = created_id
        created_id = None
        try:
            client.get_drink(deleted_id)
            print("   ОШИБКА: Ожидался 404, но ресурс был получен!")
            return 1
        except CoffeeNotFoundError:
            print("   Ожидаемая ошибка CoffeeNotFoundError (404) успешно получена.")
    except (CoffeeApiError, ValueError) as error:
        print(f"Ошибка: {error}. Метка группы: {marker}")
        return 1
    finally:
        if created_id is not None:
            try:
                client.delete_drink(created_id)
            except CoffeeNotFoundError:
                pass
            except CoffeeApiError as error:
                print(f"Не удалось удалить id={created_id}: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
