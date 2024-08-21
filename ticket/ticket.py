import json
import mysql.connector
def connect_mysql():
    con=mysql.connector.connect(
        user="root",
        password="betty520",
        host="localhost",
        database="metro"
    )
    return con
with open("tickets.json",mode="r",encoding="utf-8")as file:
    con=connect_mysql()
    data = json.load(file)
    with con.cursor(dictionary=True) as cursor:
        for row in data: 
            cursor.execute(
                """INSERT INTO Fares (originStationID, startStation, destinationStationID, endStation, normal, nwtKid, tpeKid, loveOld) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (row["originStationID"], row["startStation"], row["destinationStationID"], row["endStation"], row["Fares"]["normal"], row["Fares"]["nwtKid"], row["Fares"]["tpeKid"], row["Fares"]["loveOld"])
                )
            con.commit()
    