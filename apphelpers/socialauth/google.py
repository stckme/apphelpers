from google.auth.transport import requests
from google.oauth2 import id_token
from requests_oauthlib import OAuth2Session

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"


def fetch_info(access_token):
    session = OAuth2Session(token={"access_token": access_token})
    userinfo = session.get(GOOGLE_USERINFO_URL).json()
    return userinfo


def fetch_info_using_jwt(access_token, audience):
    request = requests.Request()
    userinfo = id_token.verify_oauth2_token(
        id_token=access_token, request=request, audience=audience
    )
    return userinfo
