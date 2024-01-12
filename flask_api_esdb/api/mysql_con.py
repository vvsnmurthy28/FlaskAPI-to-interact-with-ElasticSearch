import mysql.connector
import os
import socket

db_ip = socket.gethostbyname(os.environ.get('DB_IP'))

mydb = mysql.connector.connect(
    host = db_ip,
    user = "root",
    password = "root",
    database = "users",
    port = 3306
)

mycursor = mydb.cursor()

def check_credentials(usern,pwd):
    mycursor.execute(f'select password from credentials where username = \'{usern}\';')
    result = mycursor.fetchone()
    if result and result[0] == pwd:
        return True
    return False