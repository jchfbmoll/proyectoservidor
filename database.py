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

"""




cursor = conn.cursor()

# Execute a query
cursor.execute("SELECT VERSION()")

# Fetch result
data = cursor.fetchone()
print("MySQL Database Version:", data)

# Close connection
conn.close()
"""

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
"""
# Uso en una función
def obtener_usuarios():
    conn = get_connection()  # Obtener conexión del pool
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM usuarios")
    filas = cursor.fetchall()
    cursor.close()
    conn.close()  # Libera la conexión para que otro la use
    return filas

"""

def checkLogin(email, password):
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

def check_password(password, password_hash):
        """Verifica si la contraseña ingresada coincide con el hash almacenado."""
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

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

def get_types(table:str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = f'SELECT * FROM {table}'
        cursor.execute(query)
        filas = cursor.fetchall()
        cursor.close()
        conn.close()
        print(filas)
        return filas
    except Exception as e:
        print(e)
        return -1

def readTareas(**kwargs):
    preguntas = []
    joins = []
    if 'usuario_encargado' in kwargs:
        preguntas.append(['users.email = %s',kwargs['usuario_encargado']])
        joins.append('JOIN users ON tareas.usuario_encargado = users.id ')
    if 'estado' in kwargs:
        preguntas.append(['estadosTarea.nombre = %s',kwargs['estado']])
        joins.append('JOIN estadosTarea ON tareas.estado = estadosTarea.id ')

    if 'notEstado' in kwargs:
        preguntas.append(['estadosTarea.nombre != %s',kwargs['notEstado']])
        joins.append('JOIN estadosTarea ON tareas.estado = estadosTarea.id ')
    if 'empresa' in kwargs:
        preguntas.append(['tareas.empresa_id = %s',kwargs['empresa']])
    if 'proyectoId' in kwargs:
        preguntas.append(['tareas.proyectoId = %s',kwargs['proyectoId']])

    conn = get_connection()
    cursor = conn.cursor()
    columns = []
    placeholders = []
    values = []
    
    query = f'SELECT * FROM tareas'
    print(query)
    if joins:
        query += ' ' + ' '.join(joins)
    if preguntas:
        preg_query = ' AND '.join(p[0] for p in preguntas)
        query += f' WHERE {preg_query}'
        print(query)
        valores_query = tuple(p[1] for p in preguntas)
        print(valores_query)

        cursor.execute(query, valores_query)

    else:
        
        cursor.execute(query)
    filas = cursor.fetchall()
    print(filas)
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
        if conn:
            conn.rollback()
        print( str(e))
        return {'error': str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()