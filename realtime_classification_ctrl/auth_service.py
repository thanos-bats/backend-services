from typing import Any, Dict
import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import KEYCLOAK_ISSUER, KEYCLOAK_JWKS_URL

bearer_scheme = HTTPBearer(auto_error=False)

# Cache για τα JWKS keys για να μην κάνει HTTP request σε κάθε API call
_jwks_cache: Dict[str, Any] = {}


def _get_jwks() -> Dict[str, Any]:
    global _jwks_cache
    if not _jwks_cache:
        try:
            # Αν το Keycloak τρέχει στο ίδιο δίκτυο, φρόντισε να είναι προσβάσιμο το URL
            response = requests.get(KEYCLOAK_JWKS_URL, timeout=10)
            response.raise_for_status()
            _jwks_cache = response.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to fetch Keycloak JWKS keys: {exc}",
            )
    return _jwks_cache


def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )

    token = credentials.credentials
    jwks = _get_jwks()

    try:
        # Διαβάζουμε το unverified header για να βρούμε το Key ID ('kid')
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key.get("kid") == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key.get("use"),
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            # Αν άλλαξαν τα κλειδιά, καθαρίζουμε την cache και ξαναδοκιμάζουμε μία φορά
            _jwks_cache.clear()
            jwks = _get_jwks()
            for key in jwks.get("keys", []):
                if key.get("kid") == unverified_header.get("kid"):
                    rsa_key = key
                    break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Public key not found in Keycloak JWKS.",
            )

        # Επαλήθευση υπογραφής και claims (Issuer & Expiration)
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            issuer=KEYCLOAK_ISSUER,
            options={"verify_aud": False},  # Τα Keycloak access tokens συχνά δεν έχουν 'aud'
        )
        return payload

    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Keycloak token: {exc}",
        )
