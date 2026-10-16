import datetime
import os
from uuid import uuid4
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_URL = "https://portalpacjenta.luxmed.pl"
LOGIN_ENDPOINT = "/PatientPortal/Account/Login"
SEARCH_ENDPOINT = "/PatientPortal/NewPortal/terms/"

load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)
LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("PASSWORD")


class SessionExpiredError(Exception):
    pass


def login(
        session: requests.Session | None = None,
    ):
    login_payload: dict[str, str] = {
        "login": LOGIN,
        "password": PASSWORD
    }
    login_url = BASE_URL + LOGIN_ENDPOINT
    login_response = session.post(
        url=login_url,
        json=login_payload,
        timeout=10
    )
    login_response.raise_for_status()


def get_available_slots(
        session: requests.Session | None = None,
        service_variant_id: int = 8294,
        city: str = "Warszawa",
        ) -> dict:
    login_url = "https://portalpacjenta.luxmed.pl/PatientPortal/NewPortal/Page/Account/Login"
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
    search_response = session.get(
        url=BASE_URL+SEARCH_ENDPOINT,
        params=search_params,
        timeout=10
    )
    search_response.raise_for_status()
    if search_response.url == login_url:
        raise SessionExpiredError("Sesja wymaga ponownego logowania")
    data = search_response.json()

    return data