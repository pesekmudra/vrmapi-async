from typing import Callable, Any

from vrmapi_async.routes import VRMRoutes


class BaseNamespace:
    """Base class for API namespaces."""

    def __init__(self, request_method: Callable[..., Any], routes: VRMRoutes):
        self._request = request_method
        self.routes = routes
