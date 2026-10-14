import argparse
import datetime
import os
from uuid import uuid4
import json
import pprint

import requests
from dotenv import load_dotenv

load_dotenv()
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")
BASE_URL = "https://portalpacjenta.luxmed.pl"
LOGIN_ENDPOINT = "/PatientPortal/Account/Login"
SEARCH_ENDPOINT = "/PatientPortal/NewPortal/terms/"


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

def check_if_new_slots(current_slots: list[dict], old_slots: list[dict]) -> list[dict]:
    new_slots = []

    for slot in current_slots:
        if slot in old_slots:
            continue
        new_slots.append(slot)

    return new_slots

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


def main() -> None:
    with open("data_mock.json", "r") as file:
        data = json.load(file)
    with open("data_mock_2.json", "r") as file2:
        data_2 = json.load(file2)
    # data = get_available_slots()
    # pprint.pp(extract_slots(data))
    check_if_new_slots(current_slots=extract_slots(data), old_slots=extract_slots(data_2))


if __name__ == "__main__":
    main()