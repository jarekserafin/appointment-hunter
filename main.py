import requests
import json
import os

from uuid import uuid4
from dotenv import load_dotenv


BASE_URL = "https://portalpacjenta.luxmed.pl"
LOGIN_ENDPOINT = "/PatientPortal/Account/Login"
SEARCH_ENDPOINT = "/PatientPortal/NewPortal/terms/"

# Load variables from env
load_dotenv()
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")


def print_appointment_list(data: dict) -> None:
    available_slots_count = 0
    for day_slot in data["termsForService"]["termsForDays"]:
        available_slots_count += len(day_slot["terms"])

    print(f"Znaleziono {available_slots_count} terminów w dniach:")
    for day_slot in data["termsForService"]["termsForDays"]:
        print(day_slot["day"][0:10])


def get_available_slots():
    payload = {
        "login":LOGIN,
        "password":PASSWORD
    }

    login_url = BASE_URL + LOGIN_ENDPOINT
    search_params: dict [str, str | int]= {
        "searchPlace.id": 1,
        "searchPlace.name":"Warszawa",
        "searchPlace.type": 0,
        "serviceVariantId": 4502,
        "languageId": 10,
        "searchDateFrom": "2026-10-14",
        "searchDateTo": "2026-10-16",
        "searchDatePreset" : 3,
        "processId": str(uuid4()),
        "nextSearch": "false",
        "searchByMedicalSpecialist": "false",
        "serviceVariantSource": 2,
        "locationReplaced":"false",
        "delocalized":"false"
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

data = get_available_slots()

# with open(file="data_mock.json", mode="r", encoding="utf-8") as file:
#     data = json.load(file)

print_appointment_list(data=data)
