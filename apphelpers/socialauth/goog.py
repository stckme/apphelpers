import os
from requests_oauthlib import OAuth2Session

try:
    from converge import settings
except:
    import settings

if not settings.G_REDIRECT_URI.startswith("https"):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "True"


def fetch_info(access_token):
    session = OAuth2Session(token={"access_token": access_token})
    userinfo = session.get("https://www.googleapis.com/oauth2/v1/userinfo").json()
    return userinfo
