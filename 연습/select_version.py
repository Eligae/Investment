import pymysql

# location : C:\Program Files (x86)\Common Files\MariaDBShared\HeidiSQL\heidisql.exe
connection = pymysql.connect(host='localhost', port=3306, db='Investment_', user='root', passwd='superriaco', autocommit=True)
cursor = connection.cursor()
cursor.execute("SELECT VERSION();")
result = cursor.fetchone()
print(f"MariaDB version : {result}")
connection.close()