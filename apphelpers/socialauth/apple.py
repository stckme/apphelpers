import json
import jwt
import requests

try:
    from converge import settings
except:
    import settings


def fetch_info(token):
    json_web_key_sets = requests.get("https://appleid.apple.com/auth/keys")
    public_keys = {}
    for jwk in json_web_key_sets.json()["keys"]:
        key_id = jwk["kid"]
        public_keys[key_id] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

    key_id = jwt.get_unverified_header(token)["kid"]
    key = public_keys[key_id]
    payload = jwt.decode(
        token, key=key, audience=settings.APPLE_AUDIANCE, algorithms=["RS256"]
    )
    return payload
