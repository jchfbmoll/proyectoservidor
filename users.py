## Clases que coinciden con los datos de los usuarios de las bases de datos
from pydantic import BaseModel

class User_Login:
    def __init__(self, reg):
        self.id = reg['id']
        self.email = reg['email']
        self.hashed_password = reg['password']

class User:
    def __init__(self, reg):
        self.id = reg['id']
        self.nombre = reg['nombre']
        self.apellidos = reg['apellidos']
        self.email = reg['email']
        self.ultima_empresa_conn = reg['ultima_empresa_conn']

class UserLogin(BaseModel):
    mail: str
    password: str