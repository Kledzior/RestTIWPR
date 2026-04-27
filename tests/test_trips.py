import pytest
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time
import time


def test_create_trip_success(client, auth_headers):
    
    trip_payload = {
        "destination_name": "Berlin, Niemcy",
        "destination_lat": 52.52,
        "destination_lon": 13.41,
        "destination_timezone": "Europe/Berlin",
        
        "start_date": "2026-07-01T10:00:00Z",
        "end_date": "2026-07-10T10:00:00Z",
        
        "airline_id": None
    }

    response = client.post("/trips/", json=trip_payload, headers=auth_headers)

    assert response.status_code == 200
    
    data = response.json()
    assert data["destination_name"] == "Berlin, Niemcy"
    assert "id" in data  
    assert data["user_id"] is not None 

def test_create_trip_invalid_dates(client, auth_headers):
    bad_payload = {
        "destination_name": "Błąd Czasu",
        "destination_lat": 0, "destination_lon": 0, "destination_timezone": "UTC",
        "start_date": "2025-07-10T10:00:00Z",
        "end_date": "2025-07-01T10:00:00Z"
    }
    
    response = client.post("/trips/", json=bad_payload, headers=auth_headers)
    
    assert response.status_code == 400
    assert "Nie można planować podróży w przeszłości!" in response.json()["detail"]

def test_create_trip_unauthorized(client):
    trip_payload = {
        "destination_name": "Tajne Wakacje",
        "destination_lat": 50.0,
        "destination_lon": 20.0,
        "destination_timezone": "Europe/Warsaw",
        "start_date": "2030-01-01T12:00:00Z",
        "end_date": "2030-01-10T12:00:00Z"
    }
    
    response = client.post("/trips/", json=trip_payload)
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_create_trip_end_before_start(client, auth_headers):
    start_date = (datetime.utcnow() + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    end_date = (datetime.utcnow() + timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

    trip_payload = {
        "destination_name": "Nielogiczna Podróż",
        "destination_lat": 50.0,
        "destination_lon": 20.0,
        "destination_timezone": "UTC",
        "start_date": start_date,
        "end_date": end_date 
    }
    
    response = client.post("/trips/", json=trip_payload, headers=auth_headers)
    
    assert response.status_code == 400

    assert "Data powrotu nie może być wcześniejsza niż data wyjazdu!" in response.json()["detail"]

def test_get_trips_archive_vs_upcoming(client, auth_headers):
    

    now_utc = datetime.now(timezone.utc)
    
    short_start = (now_utc + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    short_end = (now_utc + timedelta(seconds=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    future_start = (now_utc + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    future_end = (now_utc + timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ")

    res1 = client.post("/trips/", json={
        "destination_name": "Szybki wypad",
        "destination_lat": 50.0, "destination_lon": 20.0, "destination_timezone": "UTC",
        "start_date": short_start,
        "end_date": short_end
    }, headers=auth_headers)
    assert res1.status_code == 200


    res2 = client.post("/trips/", json={
        "destination_name": "Daleka przyszłość",
        "destination_lat": 50.0, "destination_lon": 20.0, "destination_timezone": "UTC",
        "start_date": future_start,
        "end_date": future_end
    }, headers=auth_headers)
    assert res2.status_code == 200

    time.sleep(4)

    response_current = client.get("/trips/", headers=auth_headers)
    assert response_current.status_code == 200
    data_current = response_current.json()
    
    assert len(data_current) == 1
    assert data_current[0]["destination_name"] == "Daleka przyszłość"

    response_archive = client.get("/trips/?archive=true", headers=auth_headers)
    assert response_archive.status_code == 200
    data_archive = response_archive.json()
    
    assert len(data_archive) == 1
    assert data_archive[0]["destination_name"] == "Szybki wypad"


def test_trip_details(client,auth_headers):
    trip_payload = {
    "destination_name": "Berlin, Niemcy",
    "destination_lat": 52.52,
    "destination_lon": 13.41,
    "destination_timezone": "Europe/Berlin",
    
    "start_date": "2026-07-01T10:00:00Z",
    "end_date": "2026-07-10T10:00:00Z",
    
    "airline_id": None
    }

    create_response = client.post("/trips/", json=trip_payload, headers=auth_headers)
    assert create_response.status_code == 200
    trip_id = create_response.json()["id"]

    response = client.get(f"/trips/{trip_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["destination_name"] == "Berlin, Niemcy"
    received_start = datetime.fromisoformat(data["start_date"].replace('Z', '+00:00'))
    received_end = datetime.fromisoformat(data["end_date"].replace('Z', '+00:00'))
    
    expected_start = datetime(2026, 7, 1, 10, 0, 0)
    expected_end = datetime(2026, 7, 10, 10, 0, 0)

    assert received_start == expected_start
    assert received_end == expected_end

def test_edit_trip_details(client,auth_headers):
    trip_payload = {
    "destination_name": "Berlin, Niemcy",
    "destination_lat": 52.52,
    "destination_lon": 13.41,
    "destination_timezone": "Europe/Berlin",
    
    "start_date": "2026-07-01T10:00:00Z",
    "end_date": "2026-07-10T10:00:00Z",
    
    "airline_id": None
    }

    create_response = client.post("/trips/", json=trip_payload, headers=auth_headers)
    assert create_response.status_code == 200
    trip_id = create_response.json()["id"]

    new_trip_payload = {
    "destination_name": "Warszawa, Polska",
    "destination_lat": 52.14,
    "destination_lon": 13.37,
    "destination_timezone": "Europe/Warsaw",
    
    "start_date": "2026-08-01T10:00:00Z",
    "end_date": "2026-09-10T10:00:00Z",
    
    "airline_id": None
    }

    edit_response = client.patch(f"/trips/{trip_id}", json=new_trip_payload, headers=auth_headers)
    assert edit_response.status_code == 200
    data = edit_response.json()

    assert data["destination_name"] == "Warszawa, Polska"
    
    received_start = datetime.fromisoformat(data["start_date"].replace('Z', '+00:00'))
    received_end = datetime.fromisoformat(data["end_date"].replace('Z', '+00:00'))
    
    expected_start = datetime(2026, 8, 1, 10, 0, 0)
    expected_end = datetime(2026, 9, 10, 10, 0, 0)

    assert received_start == expected_start
    assert received_end == expected_end