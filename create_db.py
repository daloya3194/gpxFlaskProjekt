import mysql.connector

mydb = mysql.connector.connect(
    host="185.224.138.28",
    user="u345760943_gpx_flask_proj",
    passwd="@Test_laravel3194",
)

my_cursor = mydb.cursor()