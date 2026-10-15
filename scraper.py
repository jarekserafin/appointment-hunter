import datetime
import os
from uuid import uuid4
import json
import time
import enum
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_URL = "https://api.telegram.org/bot"
BASE_URL = "https://portalpacjenta.luxmed.pl"
LOGIN_ENDPOINT = "/PatientPortal/Account/Login"
SEARCH_ENDPOINT = "/PatientPortal/NewPortal/terms/"
not_found_message = "Brak nowych terminów"
found_message = "Znaleziono nowe terminy:"
scan_start_message = "Uruchomiono skan nowych terminów w pętli dla usługi: {service_name}"


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


def get_available_slots(
        service_variant_id: int = 8294,
        city: str = "Warszawa"
        ) -> dict:
    payload: dict[str, str] = {
        "login": LOGIN,
        "password": PASSWORD
    }
    login_url = BASE_URL + LOGIN_ENDPOINT
    start_day = datetime.date.today()
    end_day = start_day + datetime.timedelta(days=13)
    search_params: dict[str, str | int] = {
        "searchPlace.id": 1,
        "searchPlace.name": city,
        "searchPlace.type": 0,
        "serviceVariantId": service_variant_id,
        "languageId": 10,
        "searchDateFrom": start_day.isoformat(),
        "searchDateTo": end_day.isoformat(),
        "searchDatePreset": 13,
        "processId": str(uuid4()),
        "nextSearch": "false",
        "searchByMedicalSpecialist": "false",
        "serviceVariantSource": 2,
        "locationReplaced": "false",
        "delocalized": "false"
    }

    with requests.Session() as session:
        login_response = session.post(
            url=login_url,
            json=payload
        )
        login_response.raise_for_status()
        search_response = session.get(
            url=BASE_URL+SEARCH_ENDPOINT,
            params=search_params
        )
        search_response.raise_for_status()
    data = search_response.json()

    return data


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
    requests.post(url=url, params=params, timeout=10)
    return


def prepare_telegram_notification(mode: str, data: list[dict]|None = None, service_name: str = None) -> str:
    if mode == "start":
        notification = scan_start_message.format(service_name=service_name) + "\n"
    elif mode == "new":
        notification = f"{found_message}\n"
        for slot in data:
            dateTimeFrom = slot["dateTimeFrom"]
            docFirstName = slot["doctorFirstName"]
            docLastName = slot["doctorLastName"]
            clinic = slot["clinic"]
            notification += f"{dateTimeFrom[0:10]} {dateTimeFrom[11:]} {docFirstName} {docLastName} w {clinic}\n"

    return notification


def main() -> None:
    wanted_service_variant_id = 4468
    service_name = get_service_from_json(wanted_service_variant_id)
    first_scan = get_available_slots(service_variant_id=wanted_service_variant_id, city="Warszawa")
    send_telegram_notification(text=prepare_telegram_notification(mode="start", service_name=service_name))
    if len(extract_slots(first_scan)) > 0:
        send_telegram_notification(
            text=prepare_telegram_notification(mode="new", data=extract_slots(first_scan))
            )
    while True:
        time.sleep(300)
        second_scan = get_available_slots(service_variant_id=wanted_service_variant_id, city="Warszawa")
        new_slots = check_if_new_slots(
            current_slots=extract_slots(second_scan),
            old_slots=extract_slots(first_scan)
            )
        first_scan = second_scan
        if new_slots is not None:
            send_telegram_notification(text=prepare_telegram_notification(mode="new", data=new_slots))



if __name__ == "__main__":
    main()
