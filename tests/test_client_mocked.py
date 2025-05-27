# --- tests/test_client_mocked.py
import pytest
import respx
from httpx import Response

from vrmapi_async.client import VRMAsyncAPI, DEMO_USER_ID, DEMO_SITE_ID
from vrmapi_async.routes import VRMRoutes
from vrmapi_async.client.users.schema import Site, SiteExtended
from vrmapi_async.client.installations.schema import ConsumptionStatsResponse

pytestmark = pytest.mark.asyncio

BASE_URL = "https://vrmapi.victronenergy.com/v2"
paths = VRMRoutes()


DEMO_LOGIN_RESPONSE = {"token": "fake_demo_token", "idUser": DEMO_USER_ID}

SITE_NON_EXTENDED_DATA = {
    "idSite": DEMO_SITE_ID,
    "accessLevel": 1,
    "owner": True,
    "is_admin": True,
    "name": "Demo Site 1",
    "identifier": "demo1",
    "idUser": DEMO_USER_ID,
    "pvMax": 1000,
    "timezone": "Europe/Amsterdam",
    "phonenumber": None,
    "notes": None,
    "geofence": None,
    "geofenceEnabled": False,
    "realtimeUpdates": True,
    "hasMains": 1,
    "hasGenerator": 0,
    "noDataAlarmTimeout": 3600,
    "alarmMonitoring": 1,
    "invalidVRMAuthTokenUsedInLogRequest": 0,
    "syscreated": 1600000000,
    "isPaygo": 0,
    "paygoCurrency": None,
    "paygoTotalAmount": None,
    "idCurrency": 1,
    "currencyCode": "EUR",
    "currencySign": "€",
    "currencyName": "Euro",
    "inverterChargerControl": 1,
    "shared": False,
    "device_icon": "solar",
}
SITES_RESPONSE = {"success": True, "records": [SITE_NON_EXTENDED_DATA]}

SITE_EXTENDED_DATA = {
    **SITE_NON_EXTENDED_DATA,
    "tags": [],
    "extended": {"info": "extra_data"},
}
SITES_EXTENDED_RESPONSE = {"success": True, "records": [SITE_EXTENDED_DATA]}

CONSUMPTION_RESPONSE = {
    "success": True,
    "records": {
        "Pc": [[1748085554000, 1.8386]],
        "Bc": [[1748089154000, 0.0789]],
        "gc": False,
        "Gc": False,
    },
    "totals": {"Pc": 1.8386, "Bc": 0.0789, "gc": False, "Gc": False},
}


@respx.mock
async def test_demo_login_success_mocked():
    """Tests that the client can log in using demo mode."""
    respx.get(f"{BASE_URL}{paths.AUTH_DEMO}").mock(
        return_value=Response(200, json=DEMO_LOGIN_RESPONSE)
    )

    client = VRMAsyncAPI(demo=True, base_url=BASE_URL)
    await client.connect()

    assert client._auth_token == "fake_demo_token"
    assert client.user_id == DEMO_USER_ID
    assert client.is_demo is True


@respx.mock
async def test_get_user_sites_mocked():
    """Tests fetching non-extended user sites."""
    respx.get(f"{BASE_URL}{paths.AUTH_DEMO}").mock(
        return_value=Response(200, json=DEMO_LOGIN_RESPONSE)
    )
    sites_url = f"{BASE_URL}{paths.USERS_INSTALLATIONS.format(user_id=DEMO_USER_ID)}"
    respx.get(sites_url).mock(return_value=Response(200, json=SITES_RESPONSE))

    client = VRMAsyncAPI(demo=True, base_url=BASE_URL)
    async with client:
        sites = await client.users.get_installations(client.user_id)

    assert len(sites) == 1
    assert isinstance(sites[0], Site)
    assert not isinstance(sites[0], SiteExtended)
    assert sites[0].id_site == DEMO_SITE_ID
    assert sites[0].name == "Demo Site 1"
    # Pydantic v2 forbids extra fields by default if not 'allow'
    with pytest.raises(AttributeError):
        _ = sites[0].extended  # Should not exist on Site


@respx.mock
async def test_get_user_sites_extended_mocked():
    """Tests fetching extended user sites."""
    respx.get(f"{BASE_URL}{paths.AUTH_DEMO}").mock(
        return_value=Response(200, json=DEMO_LOGIN_RESPONSE)
    )
    sites_url = f"{BASE_URL}{paths.USERS_INSTALLATIONS.format(user_id=DEMO_USER_ID)}"
    respx.get(sites_url, params={"extended": "1"}).mock(
        return_value=Response(200, json=SITES_EXTENDED_RESPONSE)
    )

    client = VRMAsyncAPI(demo=True, base_url=BASE_URL)
    async with client:
        sites = await client.users.get_installations_extended(client.user_id)

    assert len(sites) == 1
    assert isinstance(sites[0], SiteExtended)
    assert sites[0].id_site == DEMO_SITE_ID
    assert sites[0].extended == {"info": "extra_data"}
    assert sites[0].tags == []


@respx.mock
async def test_get_consumption_stats_mocked():
    """Tests fetching consumption stats."""
    respx.get(f"{BASE_URL}{paths.AUTH_DEMO}").mock(
        return_value=Response(200, json=DEMO_LOGIN_RESPONSE)
    )
    stats_url = f"{BASE_URL}{paths.INSTALLATIONS_STATS.format(site_id=DEMO_SITE_ID)}"
    respx.get(stats_url, params={"type": "consumption"}).mock(
        return_value=Response(200, json=CONSUMPTION_RESPONSE)
    )

    client = VRMAsyncAPI(demo=True, base_url=BASE_URL)
    async with client:
        stats = await client.installations.get_consumption_stats(DEMO_SITE_ID)

    assert isinstance(stats, ConsumptionStatsResponse)
    assert stats.success is True
    assert stats.records.pc is not None and isinstance(stats.records.pc, list)
    assert len(stats.records.pc) == 1
    assert stats.records.pc[0].timestamp == 1748085554000
    assert stats.records.pc[0].value == 1.8386
