import os
from requests_oauthlib import OAuth2Session

try:
    from converge import settings
except:
    import settings

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "True"


def fetch_info(access_token):
    session = OAuth2Session(token={"access_token": access_token})
    info_url = "https://graph.facebook.com/me?fields=" + settings.FB_USER_FIELDS
    return session.get(info_url).json()
