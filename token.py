from datetime import datetime, timezone

import jwt


def generate_token(employee_id: int, expiry: datetime, secret: str) -> str:
    return jwt.encode({"id": employee_id, "exp": int(expiry.replace(tzinfo=timezone.utc).timestamp())}, secret,
                      algorithm="HS256").decode()


def verify_token(token: str, secret: str) -> int:
    return jwt.decode(token, secret, algorithms=["HS256"], options=dict(require=["exp"], verify_exp=True))["id"]
