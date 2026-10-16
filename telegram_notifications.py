import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_URL = "https://api.telegram.org/bot"

not_found_message = "Brak nowych terminów"
found_message = "Znaleziono nowe terminy:"
scan_start_message = (
    "Uruchomiono skan nowych terminów w pętli dla usługi: {service_name}"
)


def send_telegram_notification(text) -> None:
    url = TELEGRAM_URL + TELEGRAM_BOT_TOKEN + "/sendMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url=url, params=params, timeout=10)
    response.raise_for_status()
    return


def prepare_telegram_notification(
    mode: str, data: list[dict] | None = None, service_name: str = None
) -> str:
    if mode == "start":
        notification = (
            scan_start_message.format(service_name=service_name) + "\n"
        )
    elif mode == "new":
        notification = f"{found_message}\n"
        for slot in data:
            dateTimeFrom = slot["dateTimeFrom"]
            docFirstName = slot["doctorFirstName"]
            docLastName = slot["doctorLastName"]
            clinic = slot["clinic"]

            notification += (
                f"{dateTimeFrom[0:10]} {dateTimeFrom[11:]} "
                f"{docFirstName} {docLastName} w {clinic}\n"
            )
    return notification
