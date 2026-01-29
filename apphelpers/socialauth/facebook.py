import jwt
import json

import requests
from requests_oauthlib import OAuth2Session


TOKEN_ISSUER = "https://www.facebook.com"
GRAPH_API_URL = "https://graph.facebook.com"
PUBLIC_KEYS_URL = "https://www.facebook.com/.well-known/oauth/openid/jwks"


def fetch_info(access_token, fields):
    session = OAuth2Session(token={"access_token": access_token})
    info_url = f"{GRAPH_API_URL}/me"
    return session.get(info_url, params={"fields": fields}).json()


def fetch_info_using_jwt(token, audience):
    response = requests.get(PUBLIC_KEYS_URL)
    if not response.ok:
        # Retry once if fetching keys failed
        response = requests.get(PUBLIC_KEYS_URL)
        if not response.ok:
            raise Exception("Failed to fetch Apple public keys")
    public_keys = response.json()["keys"]

    key_id = jwt.get_unverified_header(token)["kid"]
    key = None
    for jwk in public_keys:
        if key_id == jwk["kid"]:
            key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            break
    if key is None:
        raise Exception("Failed to find matching public key")

    payload = jwt.decode(
        token,
        key=key,
        audience=audience,
        algorithms=["RS256"],
        verify=True,
        issuer=TOKEN_ISSUER,
    )
    return payload
