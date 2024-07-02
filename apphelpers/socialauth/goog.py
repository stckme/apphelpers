import os

from google.auth.transport import requests
from google.oauth2 import id_token
from requests_oauthlib import OAuth2Session

try:
    from converge import settings
except ImportError:
    import settings

if not settings.G_REDIRECT_URI.startswith("https"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "True"


def fetch_info(access_token):
    session = OAuth2Session(token={"access_token": access_token})
    userinfo = session.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
    return userinfo


def fetch_info_using_jwt(access_token):
    request = requests.Request()
    userinfo = id_token.verify_oauth2_token(
        id_token=access_token, request=request, audience=settings.G_CLIENT_ID
    )
    return userinfo
