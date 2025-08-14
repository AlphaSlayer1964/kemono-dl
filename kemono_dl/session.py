import requests

from .exceptions import DDOSGuardError


class CustomSession(requests.Session):
    def request(self, method, url, *args, **kwargs):
        response = super().request(method, url, *args, **kwargs)
        if response.status_code == 403:
            raise DDOSGuardError(url)
        content_type = response.headers["Content-Type"]
        # why is the api content type text/css and not application/json!
        if content_type == "text/css":
            response.encoding = "UTF-8"
        return response
