def _event_payload(**overrides):
    payload = {
        "external_id": "user-1",
        "title": "Reunião de alinhamento",
        "description": "Pauta semanal",
        "category": "trabalho",
        "start_time": "2026-07-10T10:00:00",
        "end_time": "2026-07-10T11:00:00",
        "location": "Sala 1",
        "meeting_link": None,
        "participants": ["a@ex.com", "b@ex.com"],
        "priority": "high",
        "reminders": [15, 60],
    }
    payload.update(overrides)
    return payload


def test_create_event_returns_created_event(client):
    response = client.post("/api/v1/calendar/events", json=_event_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Reunião de alinhamento"
    assert body["status"] == "scheduled"
    assert body["participants"] == ["a@ex.com", "b@ex.com"]
    assert body["id"] is not None


def test_get_events_returns_empty_for_unknown_user(client):
    response = client.get("/api/v1/calendar/events", params={"external_id": "ghost"})

    assert response.status_code == 200
    assert response.json() == []


def test_get_events_returns_created_events_for_user(client):
    client.post("/api/v1/calendar/events", json=_event_payload())

    response = client.get("/api/v1/calendar/events", params={"external_id": "user-1"})

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["title"] == "Reunião de alinhamento"


def test_get_events_filters_by_date(client):
    client.post(
        "/api/v1/calendar/events",
        json=_event_payload(start_time="2026-07-10T10:00:00", end_time="2026-07-10T11:00:00"),
    )
    client.post(
        "/api/v1/calendar/events",
        json=_event_payload(start_time="2026-07-11T10:00:00", end_time="2026-07-11T11:00:00"),
    )

    response = client.get(
        "/api/v1/calendar/events", params={"external_id": "user-1", "date": "2026-07-11"}
    )

    events = response.json()
    assert len(events) == 1
    assert events[0]["start_time"].startswith("2026-07-11")


def test_update_event_changes_only_provided_fields(client):
    created = client.post("/api/v1/calendar/events", json=_event_payload()).json()

    response = client.put(
        f"/api/v1/calendar/events/{created['id']}",
        json={"title": "Novo título"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Novo título"
    # Campos não enviados no PUT permanecem intactos.
    assert body["location"] == "Sala 1"


def test_update_event_returns_404_for_missing_event(client):
    response = client.put("/api/v1/calendar/events/999999", json={"title": "X"})

    assert response.status_code == 404


def test_cancel_event_sets_status_cancelled(client):
    created = client.post("/api/v1/calendar/events", json=_event_payload()).json()

    response = client.delete(f"/api/v1/calendar/events/{created['id']}")

    assert response.status_code == 200
    events = client.get(
        "/api/v1/calendar/events", params={"external_id": "user-1"}
    ).json()
    assert events[0]["status"] == "cancelled"


def test_cancel_event_returns_404_for_missing_event(client):
    response = client.delete("/api/v1/calendar/events/999999")

    assert response.status_code == 404
