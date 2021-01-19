import json
import jwt
import requests
try:
    from converge import settings
except:
    import settings

def fetch_info(token):
    jwks = requests.get('https://appleid.apple.com/auth/keys')
    public_keys = {}
    for jwk in jwks.json()['keys']:
        kid = jwk['kid']
        public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

    kid = jwt.get_unverified_header(token)['kid']
    key = public_keys[kid]
    payload = jwt.decode(token, key=key, audience=settings.APPLE_AUDIANCE, algorithms=['RS256'])
    return payload


