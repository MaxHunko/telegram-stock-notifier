import pymysql
import pandas as pd


connection = pymysql.connect(
host = "localhost",
user = "user",
password = "password",
database = "shop_data"
)

file_path = "import.xlsx"

df = pd.read_excel(file_path, sheet_name="orders")

df = df.dropna(how="all")
df = df.fillna("") 

sql = """
    INSERT INTO orders (id, pre_order_number, sku, confirmed_stock, name, phone, quantity, 
                        comment, product, url, created_at, status, np_address, checked) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

with connection.cursor() as cursor:
    for _, row in df.iterrows():
        cursor.execute(sql, tuple(row))
    connection.commit()

connection.close()