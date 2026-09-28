def test_chat_integration(client):
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Send the report to Rahul Sharma at rahul@gmail.com",
            "provider": "mock"
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["security"]["pii_detected"] is True
    assert data["security"]["entities_masked"] >= 2
    
    # The mock provider echoes back the prompt
    # Since rehydration is ON by default, the final response should contain the original PII, 
    # but the intermediate was masked.
    assert "Rahul Sharma" in data["response"]
    assert "rahul@gmail.com" in data["response"]
    
def test_mask_preview(client):
    response = client.post(
        "/api/v1/security/mask",
        json={
            "text": "My name is Rahul and email is rahul@gmail.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "[PERSON_1]" in data["masked_text"]
    assert "[EMAIL_1]" in data["masked_text"]
    assert "Rahul" not in data["masked_text"]
