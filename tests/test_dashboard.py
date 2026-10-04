"""Smoke tests: EPA AQI maths and the Flask API on the bundled sample exports (offline)."""
import os

os.environ.pop("OPENAQ_API_KEY", None)  # always test the offline snapshot path
os.environ["AQI_LIVE"] = "0"

import pytest

import app as dashboard
import live


@pytest.mark.parametrize("pm25, expected", [
    (0.0, 0),       # bottom of "Good"
    (9.0, 50),      # top of "Good" (2024 breakpoint)
    (35.4, 100),    # top of "Moderate"
    (40.6, 114),    # Unhealthy for Sensitive Groups
    (55.5, 151),    # first "Unhealthy" value
    (400.0, 500),   # off the scale clamps to 500
])
def test_pm25_sub_index_epa_2024(pm25, expected):
    assert live.sub_index("pm25", pm25, "µg/m³") == expected


def test_sub_index_rejects_unknown_unit():
    assert live.sub_index("pm25", 40.0, "ppm") is None


def test_category_labels():
    assert dashboard.aqi_category(42)["label"] == "Good"
    assert dashboard.aqi_category(114)["label"] == "Unhealthy for Sensitive Groups"


@pytest.fixture()
def client():
    return dashboard.app.test_client()


def test_index_renders(client):
    assert client.get("/").status_code == 200


@pytest.mark.parametrize("route", ["/api/summary", "/api/meta", "/api/history?days=7",
                                   "/api/predictions", "/api/forecast?hours=24"])
def test_api_routes_work_offline(client, route):
    r = client.get(route)
    assert r.status_code == 200, r.get_data(as_text=True)
    assert r.get_json()


def test_forecast_length_and_non_negative(client):
    f = client.get("/api/forecast?hours=12").get_json()
    assert len(f["pm25"]) == 12
    assert all(v >= 0 for v in f["pm25"])
