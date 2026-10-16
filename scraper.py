import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from luxmed import SessionExpiredError, get_available_slots, login

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_URL = "https://api.telegram.org/bot"
not_found_message = "Brak nowych terminów"
found_message = "Znaleziono nowe terminy:"
scan_start_message = "Uruchomiono skan nowych terminów w pętli dla usługi: {service_name}"  # noqa: E501


def get_service_from_json(service_id: int) -> str | None:
    with open("data/all_services.json", "r") as file:
        data = json.load(file)
    for item in data:
        for service in item["children"]:
            if service["id"] == service_id:
                return service["name"]
    return None


def print_appointment_list(data: dict) -> None:
    available_slots_count = 0
    for day_slot in data["termsForService"]["termsForDays"]:
        available_slots_count += len(day_slot["terms"])

    print(f"Znaleziono {available_slots_count} terminów")


def extract_slots(data: dict) -> list[dict]:
    result = []
    for day in data["termsForService"]["termsForDays"]:
        for term in day["terms"]:
            result.append({
                "scheduleId": term["scheduleId"],
                "serviceId": term["serviceId"],
                "dateTimeFrom": term["dateTimeFrom"],
                "dateTimeTo": term["dateTimeTo"],
                "doctorId": term["doctor"]["id"],
                "doctorFirstName": term["doctor"]["firstName"],
                "doctorLastName": term["doctor"]["lastName"],
                "clinicId": term["clinicId"],
                "clinic": term["clinic"],
                "isTelemedicine": term["isTelemedicine"]
            })
    return result


def check_if_new_slots(
        current_slots: list[dict],
        old_slots: list[dict]
        ) -> list[dict] | None:
    new_slots = []

    for slot in current_slots:
        if slot in old_slots:
            continue
        new_slots.append(slot)

    if len(new_slots) > 0:
        return new_slots
    return None


def send_telegram_notification(text) -> None:
    url = TELEGRAM_URL + TELEGRAM_BOT_TOKEN + "/sendMessage"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    response = requests.post(url=url, params=params, timeout=10)
    response.raise_for_status()
    return


def prepare_telegram_notification(
        mode: str,
        data: list[dict] | None = None,
        service_name: str = None
        ) -> str:
    if mode == "start":
        notification = scan_start_message.format(service_name=service_name) + "\n"  # noqa: E501
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


def main() -> None:
    with requests.Session() as session:
        login(session=session)
        wanted_service_variant_id = 4468
        service_name = get_service_from_json(wanted_service_variant_id)

        try:
            first_scan = get_available_slots(
                session=session,
                service_variant_id=wanted_service_variant_id,
                city="Warszawa"
                )

            send_telegram_notification(
                text=prepare_telegram_notification(
                    mode="start", service_name=service_name
                    )
            )
        except requests.exceptions.RequestException as e:
            print(f"Error while fetching slots or sending notification ({type(e).__name__})")  # noqa: E501
            return

        if len(extract_slots(first_scan)) > 0:
            try:
                send_telegram_notification(
                    text=prepare_telegram_notification(
                        mode="new",
                        data=extract_slots(first_scan)
                        )
                    )
            except requests.exceptions.RequestException as e:
                print(f"Error while sending notification ({type(e).__name__})")
                return

        while True:
            time.sleep(180)

            try:
                second_scan = get_available_slots(
                    session=session,
                    service_variant_id=wanted_service_variant_id,
                    city="Warszawa"
                )
                new_slots = check_if_new_slots(
                    current_slots=extract_slots(second_scan),
                    old_slots=extract_slots(first_scan)
                    )
                if new_slots is not None:
                    send_telegram_notification(
                        text=prepare_telegram_notification(mode="new", data=new_slots)  # noqa: E501
                        )
                first_scan = second_scan
            except requests.exceptions.RequestException as e:
                print(f"Error while fetching slots or sending notification ({type(e).__name__})")  # noqa: E501
                continue
            except SessionExpiredError:
                try:
                    login(session=session)
                except requests.exceptions.RequestException as e:
                    print(f"Error while logging in: ({type(e).__name__})")


if __name__ == "__main__":
    main()
