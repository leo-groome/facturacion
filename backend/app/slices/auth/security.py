import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    secret_key = os.getenv("SECRET_KEY")
    algorithm = os.getenv("ALGORITHM", "HS256")
    expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 Horas
    
    if not secret_key:
        raise RuntimeError("Configuración ausente: JWT_SECRET_KEY no definida")

    to_encode = data.copy()
    expire_timer = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire_timer})
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt
