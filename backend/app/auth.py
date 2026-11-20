"""Firebase Authentication: every API call carries a Firebase ID token (anonymous or phone sign-in)."""
import firebase_admin
from fastapi import Header, HTTPException
from firebase_admin import auth, credentials

from . import config


def _init():
    if firebase_admin._apps:
        return
    cred = None  # on Cloud Run: the service's own identity
    if config.LOCAL_ACCESS_TOKEN:  # local development: reuse the gcloud token
        from google.oauth2.credentials import Credentials

        class _Token(credentials.Base):
            def get_credential(self):
                return Credentials(token=config.LOCAL_ACCESS_TOKEN)

        cred = _Token()
    firebase_admin.initialize_app(cred, options={"projectId": config.PROJECT})


_init()


def identity(authorization: str = Header(default="")) -> dict:
    """The signed-in user: {'uid', 'anonymous'}. Anonymous = a demo session (e.g. a judge)."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in first")
    try:
        decoded = auth.verify_id_token(authorization.removeprefix("Bearer "))
    except Exception:
        raise HTTPException(401, "Your session expired. Reload the page.")
    return {"uid": decoded["uid"], "anonymous": decoded.get("firebase", {}).get("sign_in_provider") == "anonymous"}


def current_user(authorization: str = Header(default="")) -> str:
    """Returns the signed-in user's uid, or 401."""
    return identity(authorization)["uid"]
