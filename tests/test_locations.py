from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_search_locations_success(client, auth_headers):
    mock_response = [
        {
            "name": "Londyn, Wielka Brytania",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "timezone": "Europe/London"
        },
        {
            "name": "Londyn, Kanada",
            "latitude": 42.9834,
            "longitude": -81.233,
            "timezone": "America/Toronto"
        }
    ]

    with patch("weather_client.get_coordinates", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        response = client.get("/locations/search", params={"q": "Londyn"}, headers=auth_headers)

    
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    
    assert len(data) == 2
    
    assert data[0]["name"] == "Londyn, Wielka Brytania"
    assert data[0]["latitude"] == pytest.approx(51.5074)

def test_search_locations_too_short(client, auth_headers):
    response = client.get("/locations/search", params={"q": "Lo"}, headers=auth_headers)
    
    assert response.status_code == 422 

def test_search_locations_unauthorized(client):
    response = client.get("/locations/search", params={"q": "Londyn"})
    
    assert response.status_code == 401