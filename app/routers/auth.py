from datetime import datetime, timedelta, timezone
from typing import Annotated


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from ..config import config_values

# TODO, this is not a database
clients_db = {
    "first_client": {
        "disabled": False,
        "client_id": "first_client",
        "client_secret_hashed": "$2b$12$Yqwzj50q0.5brgJAYwOIEO1l10tdgStMZEB41HwRMFzU/h5wuDsh.",
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    client_id: str | None = None


class Client(BaseModel):
    """Client without the hashed secret, more suitable to view"""

    client_id: str
    disabled: bool | None = None


class ClientInDB(Client):
    """Client with hashed secret"""

    client_secret_hashed: str


secret_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()


def verify_client_secret(plain_secret, hashed_secret):
    return secret_context.verify(plain_secret, hashed_secret)


def get_secret_hash(secret):
    return secret_context.hash(secret)


def get_client(db, client_id: str):
    if client_id in db:
        client_dict = db[client_id]
        return ClientInDB(**client_dict)


def authenticate_client(clients_db, client_id: str, client_secret: str):
    client: ClientInDB = get_client(clients_db, client_id)
    if not client:
        return False
    if not verify_client_secret(client_secret, client.client_secret_hashed):
        return False
    return client


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config_values.SECRET_KEY, algorithm=config_values.ALGORITHM
    )
    return encoded_jwt


async def get_current_client(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, config_values.SECRET_KEY, algorithms=[config_values.ALGORITHM]
        )
        client_id = payload.get("sub")
        if client_id is None or not isinstance(client_id, str):
            raise credentials_exception

        token_data = TokenData(client_id=client_id)
    except JWTError:
        raise credentials_exception

    # If we get this far, the token is valid
    if token_data.client_id is None:
        raise credentials_exception
    client = get_client(clients_db, client_id=token_data.client_id)
    if client is None:
        raise credentials_exception
    return client


async def get_current_active_client(
    current_client: Annotated[Client, Depends(get_current_client)],
):
    if current_client.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_client


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    client = authenticate_client(clients_db, form_data.username, form_data.password)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config_values.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": client.client_id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me/", response_model=Client)
async def read_users_me(
    current_client: Annotated[Client, Depends(get_current_active_client)],
):
    return current_client


@router.get("/users/me/items/")
async def read_own_items(
    current_client: Annotated[Client, Depends(get_current_active_client)],
):
    return [{"item_id": "Foo", "owner": current_client.client_id}]
