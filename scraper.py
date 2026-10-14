import datetime
import os
from uuid import uuid4
import json

import requests
from dotenv import load_dotenv

load_dotenv()
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_URL = "https://api.telegram.org/bot"
BASE_URL = "https://portalpacjenta.luxmed.pl"
LOGIN_ENDPOINT = "/PatientPortal/Account/Login"
SEARCH_ENDPOINT = "/PatientPortal/NewPortal/terms/"

def print_appointment_list(data: dict) -> None:
    available_slots_count = 0
    for day_slot in data["termsForService"]["termsForDays"]:
        available_slots_count += len(day_slot["terms"])

    print(f"Znaleziono {available_slots_count} terminów")


def get_available_slots(
        service_variant_id: int = 4502,
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
        ) -> list[dict]:
    new_slots = []

    for slot in current_slots:
        if slot in old_slots:
            continue
        new_slots.append(slot)

    return new_slots


def send_telegram_notification(slots: list[dict] = None) -> None:
    url = TELEGRAM_URL + TELEGRAM_BOT_TOKEN + "/sendMessage"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "Kawa wleciała tętno jest w normie"
    }
    response = requests.post(url=url, params=params, timeout=10)
    print(response.status_code)
    print(response.json)
    return


def main() -> None:
    data = get_available_slots()
    check_if_new_slots(
        current_slots=extract_slots(data),
        old_slots=extract_slots(data_2)
        )
    send_telegram_notification()


if __name__ == "__main__":
    main()
