import pymysql
import pandas as pd

host = "localhost"
user = "user"
password = "password"
database = "shop_data"

connection = pymysql.connect(host=host, user=user, password=password, database=database)

excel_writer = pd.ExcelWriter("database_export.xlsx", engine="openpyxl")

with connection.cursor() as cursor:
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    df = pd.read_sql(f"SELECT * FROM {table}", connection)
    df.to_excel(excel_writer, sheet_name=table, index=False)

excel_writer.close()
connection.close()
