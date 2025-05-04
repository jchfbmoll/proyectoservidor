from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from database import getProyectosDB,reg_user,checkLogin,get_types,crearReg,readTareas,get_reg,updateReg,check_empresas,get_userid
import json
origins = [
   
    "*",  # Para permitir cualquier origen (NO recomendado para producción)
]

class UserLogin(BaseModel):
    mail: str
    password: str
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Lista de orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],  # Permite cualquier tipo de método HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Permite cualquier encabezado
)

@app.get('/')
def read_root():
    return {'message': 'Hola, Mundo!'}

@app.get('/tareas')
def getTareas(request:Request):
    kwargs = {}
    params = dict(request.query_params)
    if 'mail' in params:
        kwargs['usuario_encargado'] = params['mail']
    if 'estado' in params:
        kwargs['estado'] = params['estado']
    if 'notEstado' in params:
        kwargs['notEstado'] = params['notEstado']
    if 'empresa' in params:
        kwargs['empresa'] = params['empresa']
    if 'proyectoId' in params:
        kwargs['proyectoId'] = params['proyectoId']
    taskList = readTareas(**kwargs)
    tasks = []
    for task in taskList:
        print (f'prueba de {task}')
        id_reg = task['id']
        titulo = task['titulo']
        estado = task['estado']
        tasks.append([id_reg, titulo, estado])
    return tasks

@app.get('/tareas/{tarea_id}')
def read_tareas(tarea_id: int, otro: str=None):
    tarea = get_reg('tareas', tarea_id)
    return {'tarea': tarea}

@app.get('/empresas')
def getEmpresas(request:Request):
    params = dict(request.query_params)
    if 'user_id' in params:
        user_id = params['user_id']
        empresas = check_empresas(user_id)
        print(empresas)
        return empresas
    return {'error': 'Ha ocurrido un error recuperando las empresas asociadas a este usuario'}
    

@app.get('/proyectos')
def getProyectos(request:Request):
    params = dict(request.query_params)
    if 'empresa' in params:
        empresa = params['empresa']
        proyectos = getProyectosDB(empresa)
        print(proyectos)
        return proyectos
    return {'error': 'Ha ocurrido un error recuperando las empresas asociadas a este usuario'}

@app.post('/login/')
async def login(user: UserLogin):

    if checkLogin(user.mail, user.password):
        print('Contraseña correcta')
        user_reg = get_userid(user.mail)
        print(user_reg['id'])
        return {'message': f'Mail = {user.mail} Cotnraseña = {user.password}', 'valido': True, 'user_id': user_reg['id'], 'ultima_empresa_conn': user_reg['ultima_empresa_conn']}
    else:
        print('Contraseña incorrecta')
        return {'message': f'Mail = {user.mail} Cotnraseña = {user.password}', 'valido': False}
    
@app.get('/types')
async def sendTypes(request: Request):
    params = dict(request.query_params)
    if 'type' in params:
        if params['type'] :
            
            types = get_types(params['type'])
            
            return types
      

@app.post('/create')
async def crearTypes(request: Request):
    body = await request.body()
    json_data = body.decode('utf-8')
    data = json.loads(json_data)
    tabla = data['type']
    id = crearReg(tabla, data) 
    return {'id': id}

@app.post('/update')
async def actualiza(request: Request):
    body = await request.body()
    json_data = body.decode('utf-8')
    data = json.loads(json_data)
    tabla = data['type']
    id_reg = data['id']
    campo = data['campo']
    value = data['value']
    res = updateReg(tabla, id_reg, campo, value)
    if 'notError' in res:
        return {'msg': True }
    if 'error' in res:
        return {'error': f'Hubo un error actualizando el campo {campo} del registro {id} de la tabla {tabla}\nError: {res['error']}'}