import pymysql
from config import *
conn = pymysql.connect(host=HOST,user=USERNAME,password=PASSWORD,charset="utf8")
# conn = pymysql.connect(host="localhost",user="root",password="123456",charset="utf8")

cursor = conn.cursor()

sql1 = "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARSET=utf8;".format(DATABASE)
cursor.execute(sql1)

for key in SQLALCHEMY_BINDS.keys():
    sql2 = "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARSET=utf8;".format(key)
    cursor.execute(sql2)
conn.close()