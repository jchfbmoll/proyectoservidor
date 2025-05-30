from fastapi import FastAPI,Depends,HTTPException,status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime,timedelta,timezone

import traceback
from fastapi import Request
from dbfunctions import delete_allDB,getProyectosDB,reg_user,get_allDB,crearReg,readTareas,get_reg,updateReg,check_empresas,get_userid,deleteRegDB,get_regsDB,is_dev
import os
import json

from users import User,UserLogin
from typing import Annotated,Optional
import token

from validation import authenticate_user, create_access_token, create_refresh_token, validate_tokens, get_token
origins = list(set([
    "http://localhost",
    "https://localhost",
    "http://localhost:80",
    "https://localhost:443",
    "http://127.0.0.1",
    "http://127.0.0.1:80",
    "https://127.0.0.1",
    "https://127.0.0.1:443",
]))
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            # No aplicar autenticación a las pre-flight
            
            return await call_next(request)
        public_paths = {"/", "/login", '/logout', '/create', '/check-auth'}
        if request.url.path in public_paths:
            return await call_next(request)
        print(request.cookies)
        access_token, refresh_token = validate_tokens(request)
        print(access_token)
        print(refresh_token)
        if access_token:
            response = await call_next(request)
        elif refresh_token:
            # Si solo tenemos un refresh_token válido, creamos un nuevo access_token
            access_token = create_access_token(refresh_token['sub'])
            
            # Preparamos la respuesta
            response = await call_next(request)
            
            # Agregamos el nuevo access_token a la respuesta en forma de cookie
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,     # evita acceso desde JS
                secure=True,      # solo HTTPS (ajústalo a True en producción)
                samesite="None",   # previene CSRF
                path="/",
                max_age=60 * 30    # Duración del access_token
            )
        else:
            # Si no hay tokens válidos, retornamos un error
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"},
                headers={"Access-Control-Allow-Origin": 'https://localhost',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Allow-Methods':"*",  # Permite cualquier tipo de método HTTP (GET, POST, etc.)
                    'Access-Control-Allow-Headers':"*"             
                }
            )
            
        return response




app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Lista de orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],  # Permite cualquier tipo de método HTTP (GET, POST, etc.)
    allow_headers=["*"],  # Permite cualquier encabezado
)

app.add_middleware(AuthMiddleware)

@app.get('/')
def read_root():
    return {'message': 'Hola, Mundo!'}

@app.get("/check-auth")
def check_auth(request: Request):
    access_token, refresh_token = validate_tokens(request)
    
    if access_token:
        response = JSONResponse(status_code = 200,
            content= {}
        )        
        return response

    if refresh_token:
        print(refresh_token)
        access_token = create_access_token(refresh_token['sub'])
        response = JSONResponse(status_code = 200,
            content= {},
            
        )            
        response.set_cookie(key="access_token",
            value=access_token,
            httponly=True,     # evita acceso desde JS
            secure=True,       # solo HTTPS
            samesite="None", # previene CSRF
            path="/",
            max_age=60 * 30
        )
        print(response)
        return response

    raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tokens invalidos",
                headers={"Access-Control-Allow-Origin": 'https://localhost',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Allow-Methods':"*",  # Permite cualquier tipo de método HTTP (GET, POST, etc.)
                    'Access-Control-Allow-Headers':"*"             
                }
            )

@app.get('/tareas')
def getTareas(request:Request):
    def montar_filtros_init(user: User) -> list:
        print(user)
        filtros = [] 
        filtros.append([('estado', '!=', 4)])
        filtros.append([('empresa_id', '=', user['ultima_empresa_conn'])])
        filtros.append([('usuario_encargado', '=', user['id']), ('created_by', '=', user['id'])])
        return filtros
    
    def montar_filtros_proyecto(proyectoID: int, user: User) -> list|bool:
        #comprobamos que la empresa actual y la del proyecto son la misma
        proyecto = get_reg('proyectos', proyectoID)
        if proyecto['empresaid'] != user['ultima_empresa_conn']:
            return False
        filtros = [] 
        filtros.append([('proyectoId', '=', proyectoID)])
        filtros.append([('empresa_id', '=', user['ultima_empresa_conn'])])
        return filtros
        
    try:
        refresh_token = request.cookies.get('refresh_token')
        refresh_token = get_token(refresh_token)
        user_id = refresh_token['sub']
        user = get_reg('users', user_id)

        params = dict(request.query_params)

        if 'init' in params and params['init']:
            filtros = montar_filtros_init(user)
        elif 'proyectoId' in params and params['proyectoId']:
            filtros = montar_filtros_proyecto(params['proyectoId'], user)
            print('filtros')
            print(filtros)
            if not filtros:
                return JSONResponse(content={'error': f'Hubo un error recuperando las tareas del proyecto actual:  {type(e).__name__} - {e}'}, status_code=500)

        taskList = readTareas(filtros)
        tasks = []
        for task in taskList:
            print (f'prueba de {task}')
            id_reg = task['id']
            titulo = task['titulo']
            estado = task['estado']
            tasks.append([id_reg, titulo, estado])
        return JSONResponse(content={"tareas": tasks}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error recuperando las tareas:  {type(e).__name__} - {e}'}, status_code=500)


@app.get('/tareas/{tarea_id}')
def read_tareas(tarea_id: int, otro: str=None):
    tarea = get_reg('tareas', tarea_id)
    return {'tarea': tarea}

@app.get('/empresas')
def getEmpresas(request:Request):
    try:
        access_token, refresh_token = validate_tokens(request)
        user_id = access_token['sub']
        empresas = check_empresas(user_id)
        return JSONResponse(content={"empresas": empresas}, status_code=200)
    
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error actualizando:  {type(e).__name__} - {e}'}, status_code=500)

    
    
    

@app.get('/proyectos')
def getProyectos(request:Request):
    try:
        refresh_token = request.cookies.get('refresh_token')
        refresh_token = get_token(refresh_token)
        user_id = refresh_token['sub']
        user = get_reg('users', user_id)   
        proyectos = getProyectosDB(user['ultima_empresa_conn'])
        print('Lista de proyectos')
        print(proyectos)
        return JSONResponse(content={"proyectos": proyectos}, status_code=200)
    except Exception as e:

        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error recuperando los proyectos:  {type(e).__name__} - {e}'}, status_code=500)

    
    
@app.get('/all')
async def get_all(request: Request):
    try:
        params = dict(request.query_params)
        if 'tabla' in params:
            if params['tabla'] :
                types = get_allDB(params['tabla'])
                if 'error' in types:
                    raise Exception(types['error'])
                json_types = jsonable_encoder(types)
                return JSONResponse(content={"registros": json_types}, status_code=200)

            raise Exception('No se encontró el campo tabla')
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error actualizando:  {type(e).__name__} - {e}'}, status_code=500)


      
@app.get('/usuario')
async def getUsuario(request:Request):
    params = dict(request.query_params)
    if 'user_id' in params:
        reg = get_reg('users', params['user_id'])
        return {'nombre': reg['nombre'], 'apellidos':reg['apellidos'], 'email': reg['email'] }


@app.post('/admin')
async def adminFuncs(request:Request):
    data = await request.json()
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
    def enviarmail(data, mail):
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        print('enviano mail')

        # Datos del remitente
        
        correo_emisor = 'jcomasherrero@cifpfbmoll.eu'
        app_password = 'vnqw ycaw ilqz qcyq'
        url = 'http://ec2-13-36-210-54.eu-west-3.compute.amazonaws.com:443/'
        

        # Datos del destinatario
        correo_receptor = mail
        asunto = "Bienvenido a CapyGestory"
        mensaje = f'''
            Buenas {data['nombre']},
            Bievenido a CapyGestory.
            Recuerda que tu nombre de tu usuario es {mail} y tu contraseña es {data['password']}
            Puedes visitarnos desde {url}
            '''
            
          

        # Crear el mensaje
        msg = MIMEMultipart()
        msg['From'] = correo_emisor
        msg['To'] = correo_receptor
        msg['Subject'] = asunto
        msg.attach(MIMEText(mensaje, 'plain'))

        # Enviar correo
        try:
            servidor = smtplib.SMTP('smtp.gmail.com', 587)
            servidor.starttls()
            servidor.login(correo_emisor, app_password)
            servidor.send_message(msg)
            servidor.quit()
            print("Correo enviado con éxito.")
        except Exception as e:
            print(f"Error al enviar el correo: {e}")

        


    try:
        data = await request.json()
        tabla = data['tabla']
        reg_id = crearReg(tabla, data) 
        print(data)
        if data['tabla'] == 'users':
            ulid = crearReg('users_login',data)
            reg_user(ulid, data['password'])
            crearReg('usuarios_empresas', {'user_id': reg_id, 'empresa_id': data['empresa'], 'rol_id': data['tipoid']})
            #enviarmail(data, data['email'])
        return JSONResponse(content={"id":reg_id, 'mensaje': f'Registro {reg_id} de {tabla} creado correctamente'}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error creando el registro:  {type(e).__name__} - {e}'}, status_code=500)
        
@app.post('/delete')
async def deleteReg(request: Request):
    try:
        data = await request.json()
        tabla = data['tabla']
        campo = data['campo']
        valor = data['valor']

        if data['tabla'] == 'users':
            deleteRegDB('users_login', data['campo'],  data['valor'])  
            deleteRegDB('usuarios_empresas', 'user_id',  data['valor'])

        elif data['tabla'] == 'empresa':
            deleteRegDB('usuarios_empresas', 'empresa_id', data['valor'])
            deleteRegDB('proyectos', 'empresaid',  data['valor'])
            deleteRegDB('tareas', 'empresaid',  data['valor'])

        deleteRegDB(tabla, campo, valor) 

        return JSONResponse(content={'content': f'Registro {valor} de {tabla} eliminado correctamente'}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error eliminando el registro:  {type(e).__name__} - {e}'}, status_code=500)

@app.post('/update')
async def actualiza(request: Request):
    data = await request.json()
    tabla = data['type']
    id_reg = data['id']
    campo = data['campo']
    value = data['value']
    res = updateReg(tabla, id_reg, campo, value)
    if 'notError' in res:
        return {'msg': True }
    if 'error' in res:
        return {'error': f'Hubo un error actualizando el campo {campo} del registro {id} de la tabla {tabla}\nError: {res['error']}'}

@app.post('/deleteall')
async def delete_all(request: Request):
    try:
        data = await request.json()
        tabla = data['tabla']
        res = delete_allDB(tabla)
        res = {}
        if 'error' in res:
            raise Exception(res['error'])
        
        return JSONResponse(content={'mensaje': f'Tabla {tabla} reiniciada correctamente '}, status_code=200)

    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error borrando la tabla:  {type(e).__name__} - {e}'}, status_code=500)





@app.post('/login')
async def login(request: Request, form_data: Optional[UserLogin] = None):
    
    if form_data:
        user = authenticate_user(form_data.mail, form_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
    
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        response = JSONResponse(status_code = 200,
            headers={"Access-Control-Allow-Origin": 'https://localhost',
                'Access-Control-Allow-Credentials': 'true',
                'Access-Control-Allow-Methods':"*",  # Permite cualquier tipo de método HTTP (GET, POST, etc.)
                'Access-Control-Allow-Headers':"*"             
            },
            content= {},
            
        )
                
        response.set_cookie(key="access_token",
            value=access_token,
            httponly=True,     # evita acceso desde JS
            secure=True,       # solo HTTPS
            samesite="None", # previene CSRF
            path="/",
            max_age=60 * 30
        )
        response.set_cookie(key="refresh_token",
            value=refresh_token,
            httponly=True,     # evita acceso desde JS
            secure=True,       # solo HTTPS
            samesite="None", # previene CSRF
            path="/",
            max_age=60 * 60 * 24 * 180
        )
        return response
    
    raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"Access-Control-Allow-Origin": 'https://localhost',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Allow-Methods':"*",  # Permite cualquier tipo de método HTTP (GET, POST, etc.)
                    'Access-Control-Allow-Headers':"*"             
                }
               
            )


@app.post('/logout')
def logout(request: Request):
    access_token, refresh_token = validate_tokens(request)

    response = JSONResponse(status_code = 200,
        content= {}
    )

    response.set_cookie(key="access_token",
            value=access_token,
            httponly=True,     # evita acceso desde JS
            secure=True,       # solo HTTPS
            samesite="None", # previene CSRF
            path="/",
            expires=datetime.now(timezone.utc) - timedelta(days=1)
        )
    response.set_cookie(key="refresh_token",
            value=refresh_token,
            httponly=True,     # evita acceso desde JS
            secure=True,       # solo HTTPS
            samesite="None", # previene CSRF
            path="/",
            expires=datetime.now(timezone.utc) - timedelta(days=1)
        )

    return response
    
@app.get('/me')
def me(request: Request):
    refresh_token = request.cookies.get('refresh_token')
    refresh_token = get_token(refresh_token)
    user_id = refresh_token['sub']
    user = get_reg('users', user_id)
    if is_dev(user_id):
        user['rol'] = 1
    else:
        filtros = []
        filtros.append([('user_id', '=', user_id)])
        filtros.append([('empresa_id', '=', user['ultima_empresa_conn'])])
        rol = get_regsDB('usuarios_empresas', filtros)
        print(rol)
        if len(rol)>0:
            user['rol'] = rol[0]['rol_id']
        else:
            user['rol'] = 0
    return JSONResponse(content={'user': user}, status_code=200)

@app.get('/filtros')
def filtros(request: Request):
    try:
        refresh_token = request.cookies.get('refresh_token')
        refresh_token = get_token(refresh_token)
        user_id = refresh_token['sub']
        user = get_reg('users', user_id)

        params = dict(request.query_params)
        if 'filtroId' in params:
            if params['filtroId'] == 1:
                campo = 'usuario_encargado'
            elif params['filtroId'] == 2:
                campo = 'proyectoId'
        filtros = []
        filtros.append([(campo, 'is', None)])
        filtros.append([('empresa_id', '=', user['ultima_empresa_conn'])])
        taskList = readTareas(filtros)
        tasks = []
        for task in taskList:
            print (f'prueba de {task}')
            id_reg = task['id']
            titulo = task['titulo']
            estado = task['estado']
            tasks.append([id_reg, titulo, estado])
        return JSONResponse(content={"tareas": tasks}, status_code=200)
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error recuperando las tareas:  {type(e).__name__} - {e}'}, status_code=500)


@app.get('/filtrarTareas')
def filtrarTareas(request: Request):
     try:
        refresh_token = request.cookies.get('refresh_token')
        refresh_token = get_token(refresh_token)
        user_id = refresh_token['sub']
        user = get_reg('users', user_id)

        params = dict(request.query_params)
        if 'filtros' in params:
            taskList = get_regsDB('tareas', params['filtros'])
            tasks = []
            for task in taskList:
                print (f'prueba de {task}')
                id_reg = task['id']
                titulo = task['titulo']
                estado = task['estado']
                proyecto = task['proyectoId']
                tipo = task['tipo_id']
                usuario_encargado = task['usuario_encargado']
                created_by = task['created_by']
                
                tasks.append([id_reg, titulo, estado,tipo,proyecto, usuario_encargado,created_by])

            return JSONResponse(content={"tareas": tasks}, status_code=200)

     except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error filtrando las tareas:  {type(e).__name__} - {e}'}, status_code=500)   

@app.get('/getregistros')
def getregistros(request: Request):
    def custom_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    try:
        params = dict(request.query_params)
        if 'filtros' and 'tabla' in params:
            registros = get_regsDB(params['tabla'], json.loads(request.query_params.get("filtros")))
            print(registros)
            for r in registros:
                for k, v in r.items():
                    if isinstance(v, datetime):
                        r[k] = v.isoformat()
            return JSONResponse(content={"registros": registros}, status_code=200)
        
        return JSONResponse(content={'error': f'Hubo un error generando la petición de registros:  {type(e).__name__} - {e}'}, status_code=500)   

    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error recuperando los registros:  {type(e).__name__} - {e}'}, status_code=500)   


@app.get('/getreg')
def getreg(request:Request):
    try:
        params = dict(request.query_params)
        if 'id' and 'tabla' in params:
            registro = get_reg(params['tabla'], params['id'])
            return JSONResponse(content={"registro": registro}, status_code=200)
        
        return JSONResponse(content={'error': f'Hubo un error generando la petición del registro:  {type(e).__name__} - {e}'}, status_code=500)   

    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')
        return JSONResponse(content={'error': f'Hubo un error recuperando el registro:  {type(e).__name__} - {e}'}, status_code=500)   

        

