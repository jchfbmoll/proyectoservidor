import bcrypt
from users import User,User_Login
import dbfunctions
import uuid
from jose import jwt
from datetime import datetime,timedelta,timezone
import token
from jose.exceptions import ExpiredSignatureError, JWTError

from fastapi import Request
''' 
    Módulo que auténtica el usuario mediante petición a base de datos y luego mediante bcryp.checkpw 
    comprueba si la contraseña es correcta o no

'''
def authenticate_user(username: str, password: str) -> any:
    user_login = dbfunctions.get_user_login(username)
    print(user_login)
    if not user_login:
        return False
    user = User_Login(user_login)
    print(f'Usuario: {user.__dict__}')


    print(f'Usuario: {vars(user)}')
    if not user:
        return False
    if verify_password(password, user.hashed_password):
        return User(dbfunctions.get_reg('users', user.id))
    return False
        
def verify_password(password: str, password_hash: str) -> bool:
    '''
        Verifica si la contraseña ingresada coincide con el hash almacenado
    '''
    print(f'passowrd: {password_hash}')
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


''' Modulo para los tokens de validacion '''

ACCESS_SECRET_KEY = '7c18ff85f16a0f98d8e631e98907667bcb2c187f3628578bb1f697eb32c5981d'
REFRESH_SECRET_KEY = '7c18ff85f16a0f98d8e631e98907667bcb2c187f3628578bb1f697eb32c5981d'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 180

def create_access_token(user_id: int) -> token:
    payload = {}
    print('Generamos access_token')
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {}
    payload['sub'] = str(user_id)
    payload['exp'] = int(expire.timestamp())

    token = jwt.encode(payload, ACCESS_SECRET_KEY, algorithm=ALGORITHM)

    return token
    


def create_refresh_token(user_id: str):
    # 1. Calcula expiración y conviértela a UNIX timestamp
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())

    # 3. Construye el payload con exp como entero
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "exp": int(expire.timestamp())
    }

    print('Generamos refresh token')
    token = jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

    return token

create_refresh_token("usuario123")
def validate_tokens(request:Request):

    access_token = request.cookies.get('access_token')
    if access_token:
        try:
            access_token = jwt.decode(access_token, ACCESS_SECRET_KEY, algorithms=[ALGORITHM])
            print("Token válido:", access_token)
        except ExpiredSignatureError:
            access_token = None
            print("El token ha expirado")
        except JWTError:
            access_token = None
            print("Token inválido")

    refresh_token = request.cookies.get('refresh_token')
    if refresh_token:
        try:
            refresh_token = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
            print("Token válido:", refresh_token)

        except ExpiredSignatureError:
            refresh_token = None
            print("El token ha expirado")
        except JWTError:
            refresh_token = None
            print("Token inválido")

    return access_token, refresh_token

def get_token(token: token, key: str = ACCESS_SECRET_KEY, algorithm = ALGORITHM) -> token:
    try:
        token = jwt.decode(token, key, algorithms=[algorithm])

    except ExpiredSignatureError:
        token = None
    except JWTError:
        token = None

    return token