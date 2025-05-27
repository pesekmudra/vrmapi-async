# --- tests/test_client_online.py
import pytest
from vrmapi_async.client import VRMAsyncAPI, DEMO_SITE_ID
from vrmapi_async.exceptions import VRMAPIError
from vrmapi_async.client.users.schema import Site, SiteExtended
from vrmapi_async.client.installations.schema import ConsumptionStatsResponse

pytestmark = pytest.mark.asyncio


async def test_demo_login_success_online():
    """Tests that the client can log in using the *real* demo mode."""
    client = VRMAsyncAPI(demo=True)
    try:
        await client.connect()
        assert client._auth_token is not None
        assert isinstance(client.user_id, int)
    except VRMAPIError as e:
        pytest.fail(f"Online demo login failed: {e}")
    finally:
        await client.aclose()


async def test_get_user_sites_online():
    """Tests fetching non-extended sites from the *real* demo API."""
    client = VRMAsyncAPI(demo=True)
    async with client:
        sites = await client.users.get_installations(client.user_id)

    assert isinstance(sites, list)
    assert len(sites) > 0
    assert isinstance(sites[0], Site)
    # Check if a known field exists and has the right type
    assert isinstance(sites[0].id_site, int)
    assert isinstance(sites[0].name, str)


async def test_get_user_sites_extended_online():
    """Tests fetching extended sites from the *real* demo API."""
    client = VRMAsyncAPI(demo=True)
    async with client:
        sites = await client.users.get_installations_extended(client.user_id)

    assert isinstance(sites, list)
    assert len(sites) > 0  # Demo user should have sites
    assert isinstance(sites[0], SiteExtended)
    assert isinstance(sites[0].id_site, int)
    # Extended response often includes 'tags'
    assert hasattr(sites[0], "tags")


async def test_get_consumption_stats_online():
    """Tests fetching consumption stats from the *real* demo API."""
    client = VRMAsyncAPI(demo=True)
    async with client:
        # We need a site ID known to be in the demo account. Let's use 2286
        stats = await client.installations.get_consumption_stats(DEMO_SITE_ID)

    assert isinstance(stats, ConsumptionStatsResponse)
    assert stats.success is True
    assert stats.records is not None
    # We can't guarantee 'Pc' will exist, but we can check the structure
    assert hasattr(stats.records, "pc") or hasattr(stats.records, "bc")
