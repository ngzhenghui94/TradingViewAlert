# ----------------------------------------------- #
# Plugin Name           : TradingView-Webhook-Bot #
# Author Name           : fabston                 #
# File Name             : main.py                 #
# ----------------------------------------------- #

import json
import time
import re
from flask import Flask, request
from datetime import datetime, timedelta, timezone
import config
from handler import *
import mysql.connector as mysql
import mysql.connector.pooling as pooling
db_config = {
    "host":"localhost",
    "user":"root",
    "passwd":"root",
    "database":"danielninetyfour",
    "port":11115,
    "pool_size":20
}
# Create the connection pool
pool = pooling.MySQLConnectionPool(**db_config)


app = Flask(__name__)


def get_timestamp():
    gmt8 = timezone(timedelta(hours=8))
    timestamp = datetime.utcnow().replace(microsecond=0).astimezone(gmt8).replace(tzinfo=None)
    return timestamp
    
def updateDb(msg):
    db = pool.get_connection()
    cursor = db.cursor()
    msgTime = get_timestamp()
    match = re.search(r'\*#(.*)\*', msg)


    if match:
        ticker = str(match.group(1))
    if "Hull Suite" in msg:
        if "Trending Down" in msg:
            query = "UPDATE stocks SET hullsuite='Down', hslastupdated=%s where ticker=%s"
        elif "Trending Up" in msg:
            query = "UPDATE stocks SET hullsuite='Up', hslastupdated=%s where ticker=%s"
    if "Chandelier" in msg:
        if "Sell" in msg:
            query = "UPDATE stocks SET chandelier='Sell', clastupdated=%s where ticker=%s"
        elif "Buy" in msg:
            query = "UPDATE stocks SET chandelier='Buy', clastupdated=%s where ticker=%s"
    values = (msgTime, ticker)
    try:
        cursor.execute(query, values)   
        db.commit() 
        cursor.close()
        db.close()
    except Exception as e:
        print("Error: " + str(e))
        cursor.close()
        db.close()


@app.route("/webhook", methods=["POST"])
def webhook():
    print("Called")
    try:
        if request.method == "POST":
            data = request.get_json()
            key = data["key"]
            if key == config.sec_key:
                print(get_timestamp(), "Alert Received & Sent!")
                send_alert(data)
                print(data["msg"])
                updateDb(data["msg"])
                return "Sent alert", 200
            else:
                print("[X]", get_timestamp(), "Alert Received & Refused! (Wrong Key)")
                return "Refused alert", 400

    except Exception as e:
        print("[X]", get_timestamp(), "Error:\n>", e)
        return "Error", 400

@app.route("/test", methods=["get"])
def test():
    print("Called")
    return "Test", 200


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=80)
