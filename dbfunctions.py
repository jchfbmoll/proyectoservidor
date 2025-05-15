import MySQLdb
from MySQLdb.cursors import DictCursor
from MySQLdb import MySQLError
from dbutils.pooled_db import PooledDB  # Librería para manejar un pool de conexiones
import traceback
import bcrypt
import os
from dotenv import load_dotenv
import json


load_dotenv()

# Ahora puedes acceder a las variables
DBHOST = os.getenv('DBHOST')
DBUSER = os.getenv('DBUSER')
DBPASS = os.getenv('DBPASS')
DBNAME = os.getenv('DBNAME')

# Crear el pool de conexiones (configura el tamaño según la carga)
pool = PooledDB(
    MySQLdb,
    maxconnections=5,  # Máximo de conexiones simultáneas
    host=DBHOST,
    user=DBUSER,
    passwd=DBPASS,
    db=DBNAME,
    cursorclass = DictCursor
)

# Obtener una conexión del pool
def get_connection():
    return pool.connection()

def get_user_login(email: str):
    conn = get_connection()
    cursor = conn.cursor()

    # Consulta con placeholder (%s)
    query = "SELECT * FROM users_login WHERE email = %s"
    cursor.execute(query, (email,))  # Importante: pasar los valores como una tupla

    # Obtener los resultados
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def authenticate_user(email, password) -> any:
    conn = get_connection()
    cursor = conn.cursor()

    # Consulta con placeholder (%s)
    query = "SELECT password FROM users_login WHERE email = %s"
    cursor.execute(query, (email,))  # Importante: pasar los valores como una tupla

    # Obtener los resultados
    filas = cursor.fetchone()
    cursor.close()
    conn.close()
    print(filas)
    if filas:
        return check_password(password, filas['password'])
    return False
    # Cerrar la conexión
    

def reg_user(user_id, password):
    # Generar un hash seguro
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    conn = get_connection()
    cursor = conn.cursor()
    # Insertar en la base de datos
    query = "UPDATE users_login SET password = %s WHERE id = %s"
    cursor.execute(query, (hashed_password,user_id,))

    # Guardar cambios
    conn.commit()
    cursor.close()
    conn.close()



def crearReg(tabla, data):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {tabla} LIMIT 0')
        column_names = [desc[0] for desc in cursor.description]
        columns = []
        placeholders = []
        values = []
        for key,value in data.items():
            if key not in column_names:
                continue
            columns.append(key)
            placeholders.append(f'%s')
            values.append(value)
        columns = ', '.join(columns)
        placeholders = ', '.join(placeholders)
        values = tuple(values)
        print(tabla, columns, placeholders, values)
        query = f'INSERT INTO {tabla} ({columns}) VALUES ({placeholders})'
        print(query)
        cursor.execute(query, values)
        id_gen = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return id_gen

    except Exception as e:
        print(e) 
        return -1
        
def get_reg(tabla: str, id: int):
    conn = get_connection()
    cursor = conn.cursor()
    query = f'SELECT * FROM {tabla} where id = %s'
    cursor.execute(query, (id,))
    reg = cursor.fetchone()
    return reg

def get_regsDB(tabla: str, filtros: list) -> any:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        columns = []
        placeholders = []
        values = []
        print(tabla)
        print(filtros)
        query = f'SELECT * FROM {tabla}'

        if filtros:
            preg_query = ' AND '.join(f'{f[0]} {f[1]} %s' for f in filtros)
            query += f' WHERE {preg_query}'
            valores_query = tuple(f[2] for f in filtros)
            print(tabla)
            print(query)
            print(valores_query)

            cursor.execute(query, valores_query)

        else:
            
            cursor.execute(query)
        regs = cursor.fetchall()
        cursor.close()
        conn.close()
        print('registros')
        print(regs)
        print('registros')

        return regs
    except Exception as e:
        traceback.print_exc()
        print(f'Error  {type(e).__name__} - {e}')

def get_allDB(table:str):

    cursor = None
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = f'SELECT * FROM {table}'
        cursor.execute(query)
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        return filas
    except MySQLError as e:
        print( str(e))
        return {'error': str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def readTareas(filtros):
    def montar_filtros(filtros):
        resp = []
        for f in filtros:
            if len(f) == 1:
                if f[0][2]:
                    resp.append(f'{f[0][0]} {f[0][1]} %s')
                else:
                    resp.append(f'{f[0][0]} {f[0][1]} Null')
            else:
                or_group = ' OR '.join(f'{g[0]} {g[1]} %s' for g in f)
                resp.append(f'({or_group})')
        return resp
    def montar_valores(filtros):
        resp = []
        for f in filtros:
            if len(f) == 1:
                if f[0][2]:
                    resp.append(f[0][2])
            else:
                resp.extend(g[2] for g in f)
        print(resp)
        return resp

            
    filtros_query = montar_filtros(filtros)
    joins = []

    conn = get_connection()
    cursor = conn.cursor()
    columns = []
    placeholders = []
    values = []
    
    query = f'SELECT * FROM tareas'
    print(query)
    if joins:
        query += ' ' + ' '.join(joins)
    if filtros:
        preg_query = ' AND '.join(f for f in filtros_query)
        query += f' WHERE {preg_query}'
        valores_query = tuple(montar_valores(filtros))
        print(query)
        print(valores_query)

        cursor.execute(query, valores_query)

    else:
        
        cursor.execute(query)
    filas = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return filas

def updateReg(tabla:str, id_reg:int, campo:str, value: any):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = f'UPDATE {tabla} SET {campo} = %s WHERE id = %s'

        cursor.execute(query, (value,id_reg,))
        conn.commit()
        cursor.close()
        conn.close()
        return {'notError':True}
    except MySQLError as e:
        db.rollback()
        if cursor:
            cursor.close()
        if db:
            db.close()
        return {'error': e}

def check_empresas(user_id:int):
    def is_dev(user_id:int, tabla = 'usuarios_empresas', empresa_id = 1):
        conn = get_connection()
        cursor = conn.cursor()
        query = f'SELECT * FROM {tabla} where user_id = %s and empresa_id = %s and rol_id in (%s, %s)'
        cursor.execute(query, (user_id, empresa_id, 1, 2,))
        res = cursor.fetchall()
        cursor.close()
        conn.close()
        if res:
            return True
        return False

    conn = get_connection()
    cursor = conn.cursor()
    if is_dev(user_id):
       
        query = 'SELECT * from empresa'
        res = cursor.execute(query)
    else:   
        query = 'SELECT * FROM empresa JOIN usuarios_empresas ON empresa.id = usuarios_empresas.empresa_id WHERE user_id = %s  '
        res = cursor.execute(query, (user_id,))
        
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    print(res)
    return res

def getProyectosDB(empresa:int):
    

    conn = get_connection()
    cursor = conn.cursor()
      
    query = 'SELECT * FROM proyectos WHERE empresaid = %s  '
    res = cursor.execute(query, (empresa,))
        
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    print(res)
    return res


def get_userid(mail):
    conn = get_connection()
    cursor = conn.cursor()
    query = 'SELECT id, ultima_empresa_conn FROM users WHERE email = %s'
    cursor.execute(query, (mail,))
    res = cursor.fetchone()
    print(f'prueba de {res}')
    cursor.close()
    conn.close()
    return res


def deleteRegDB(tabla, campo, value):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = f'DELETE FROM {tabla} WHERE {campo} = %s'
        print(query,value)
        cursor.execute(query,(value,))
        conn.commit() 
        cursor.close()
        conn.close()
        return 
    except MySQLError as e:
        print( str(e))
        if conn:
            conn.rollback()
        return {'error': str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_allDB(tabla):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = f'DELETE FROM {tabla}'
        cursor.execute(query)
        query = f'ALTER TABLE {tabla} AUTO_INCREMENT = 1'
        cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()
        return 
    except MySQLError as e:
        if conn:
            conn.rollback()
        return {'error': str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()