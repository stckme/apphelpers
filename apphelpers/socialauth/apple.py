import json

import jwt
import requests

try:
    from converge import settings
except ImportError:
    import settings


PUBLIC_KEYS_URL = "https://appleid.apple.com/auth/keys"
TOKEN_ISSUER = "https://appleid.apple.com"


def fetch_info(token):
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
        audience=settings.APPLE_AUDIANCE,
        algorithms=["RS256"],
        verify=True,
        issuer=TOKEN_ISSUER,
    )
    return payload
