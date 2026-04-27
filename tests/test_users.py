
def test_create_user_success(client):
    """Sprawdza, czy można poprawnie zarejestrować użytkownika"""
    user_payload = {
        "email": "nowy@test.pl",
        "password": "super_tajne_haslo"
    }
    
    response = client.post("/users/create_user/", json=user_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "nowy@test.pl"
    assert "id" in data
    assert "password" not in data 

def test_create_user_duplicate_email(client):
    user_payload = {"email": "duplikat@test.pl", "password": "123"}
    
    client.post("/users/create_user/", json=user_payload)
    
    response = client.post("/users/create_user/", json=user_payload)
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Email już zarejestrowany"

def test_read_users_me_success(client):
    email = "profil@test.pl"
    password = "mocnehaslo123"
    
    client.post("/users/create_user/", json={"email": email, "password": password})
    
    login_response = client.post("/token", data={"username": email, "password": password})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/me", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == email

def test_read_users_me_unauthorized(client):
    response = client.get("/users/me")
    assert response.status_code == 401