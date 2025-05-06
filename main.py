from fastapi import FastAPI
from fastapi.responses import JSONResponse
import traceback
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from database import getProyectosDB,reg_user,checkLogin,get_types,crearReg,readTareas,get_reg,updateReg,check_empresas,get_userid,deleteRegDB
import os


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
      
@app.get('/usuario')
async def getUsuario(request:Request):
    params = dict(request.query_params)
    if 'user_id' in params:
        reg = get_reg('users', params['user_id'])
        return {'nombre': reg['nombre'], 'apellidos':reg['apellidos'], 'email': reg['email'] }

@app.post('/admin')
async def adminFuncs(request:Request):
    print('Funciones de administrador')
    data = await request.json()
    print(data)
    try:
        if 'func' in data:
            if data['func'] == 'updatePass':
                reg_user(data['user_id'], data['newPass'])
                return JSONResponse(content={"mensaje": "Contraseña actualizada correctamente"}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error actualizando:  {type(e).__name__} - {e}'}, status_code=500)
        





@app.post('/create')
async def crearTypes(request: Request):
    try:
        data = await request.json()
        tabla = data['type']
        user_id = crearReg(tabla, data) 

        if data['type'] == 'users':
            crearReg('users_login',data)
            reg_user(user_id, data['password'])
            crearReg('usuarios_empresas', {'user_id': user_id, 'empresa_id': data['empresa'], 'rol_id': data['tipoid']})

        return JSONResponse(content={"id":user_id, 'mensaje': f'Registro {user_id} de {tabla} creado correctamente'}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error creando el registro:  {type(e).__name__} - {e}'}, status_code=500)
        
@app.post('/delete')
async def deleteReg(request: Request):
    try:
        data = await request.json()
        tabla = data['type']
        print (data)
        if data['type'] == 'users':
            deleteRegDB('users_login', data['campo'], data[data['campo']])  
            deleteRegDB('usuarios_empresas', 'user_id',  data[data['campo']])

        if data['type'] == 'empresa':
            deleteRegDB('usuarios_empresas', 'empresa_id',  data[data['campo']])
            deleteRegDB('proyectos', 'empresaid',  data[data['campo']])

        deleteRegDB(tabla, data['campo'], data[data['campo']]) 

        return JSONResponse(content={'mensaje': f'Registro {data[data['campo']]} de {tabla} eliminado correctamente'}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error creando el registro:  {type(e).__name__} - {e}'}, status_code=500)

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