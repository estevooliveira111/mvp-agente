def _event_payload(**overrides):
    payload = {
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


def test_create_event_requires_auth(client):
    response = client.post("/api/v1/calendar/events", json=_event_payload())

    assert response.status_code == 401


def test_create_event_returns_created_event(client, auth_headers):
    response = client.post(
        "/api/v1/calendar/events", json=_event_payload(), headers=auth_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Reunião de alinhamento"
    assert body["status"] == "scheduled"
    assert body["participants"] == ["a@ex.com", "b@ex.com"]
    assert body["id"] is not None


def test_create_event_rejects_end_before_start(client, auth_headers):
    response = client.post(
        "/api/v1/calendar/events",
        json=_event_payload(start_time="2026-07-10T11:00:00", end_time="2026-07-10T10:00:00"),
        headers=auth_headers,
    )

    assert response.status_code == 422


def test_get_events_returns_empty_when_no_events(client, auth_headers):
    response = client.get("/api/v1/calendar/events", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_get_events_returns_created_events_for_user(client, auth_headers):
    client.post("/api/v1/calendar/events", json=_event_payload(), headers=auth_headers)

    response = client.get("/api/v1/calendar/events", headers=auth_headers)

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["title"] == "Reunião de alinhamento"


def test_get_events_filters_by_date(client, auth_headers):
    client.post(
        "/api/v1/calendar/events",
        json=_event_payload(start_time="2026-07-10T10:00:00", end_time="2026-07-10T11:00:00"),
        headers=auth_headers,
    )
    client.post(
        "/api/v1/calendar/events",
        json=_event_payload(start_time="2026-07-11T10:00:00", end_time="2026-07-11T11:00:00"),
        headers=auth_headers,
    )

    response = client.get(
        "/api/v1/calendar/events", params={"date": "2026-07-11"}, headers=auth_headers
    )

    events = response.json()
    assert len(events) == 1
    assert events[0]["start_time"].startswith("2026-07-11")


def test_get_events_rejects_invalid_date(client, auth_headers):
    response = client.get(
        "/api/v1/calendar/events", params={"date": "not-a-date"}, headers=auth_headers
    )

    assert response.status_code == 400


def test_get_events_only_returns_own_events(client, auth_headers, other_user_auth_headers):
    client.post("/api/v1/calendar/events", json=_event_payload(), headers=auth_headers)

    response = client.get("/api/v1/calendar/events", headers=other_user_auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_update_event_changes_only_provided_fields(client, auth_headers):
    created = client.post(
        "/api/v1/calendar/events", json=_event_payload(), headers=auth_headers
    ).json()

    response = client.put(
        f"/api/v1/calendar/events/{created['id']}",
        json={"title": "Novo título"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Novo título"
    # Campos não enviados no PUT permanecem intactos.
    assert body["location"] == "Sala 1"


def test_update_event_returns_404_for_missing_event(client, auth_headers):
    response = client.put(
        "/api/v1/calendar/events/999999", json={"title": "X"}, headers=auth_headers
    )

    assert response.status_code == 404


def test_update_event_returns_404_for_another_users_event(
    client, auth_headers, other_user_auth_headers
):
    created = client.post(
        "/api/v1/calendar/events", json=_event_payload(), headers=auth_headers
    ).json()

    response = client.put(
        f"/api/v1/calendar/events/{created['id']}",
        json={"title": "Tentativa de invasão"},
        headers=other_user_auth_headers,
    )

    assert response.status_code == 404


def test_cancel_event_sets_status_cancelled(client, auth_headers):
    created = client.post(
        "/api/v1/calendar/events", json=_event_payload(), headers=auth_headers
    ).json()

    response = client.delete(
        f"/api/v1/calendar/events/{created['id']}", headers=auth_headers
    )

    assert response.status_code == 200
    events = client.get("/api/v1/calendar/events", headers=auth_headers).json()
    assert events[0]["status"] == "cancelled"


def test_cancel_event_returns_404_for_missing_event(client, auth_headers):
    response = client.delete("/api/v1/calendar/events/999999", headers=auth_headers)

    assert response.status_code == 404


def test_cancel_event_returns_404_for_another_users_event(
    client, auth_headers, other_user_auth_headers
):
    created = client.post(
        "/api/v1/calendar/events", json=_event_payload(), headers=auth_headers
    ).json()

    response = client.delete(
        f"/api/v1/calendar/events/{created['id']}", headers=other_user_auth_headers
    )

    assert response.status_code == 404
