#!/usr/bin/python
import psycopg2
import json
from config import config
import suspengine
import chat
import initializedb

initializedb.initialize()
app = suspengine
iden = 0

@app.channel("login")
def login(c, addr, data):
    dbuid = None
    print('Data Received')
    tempid = app.callvariable("id", c)
    tempuid = data['userid']
    temppw = data['pword']
    tempstate = data['state']
    conn = psycopg2.connect(database = "logindb", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5432")
    print("Opened database successfully")
    cur = conn.cursor()
    cur.execute("SELECT id, userid, pword, state  from LOGIN WHERE userid = '" + tempuid + "'")
    rows = cur.fetchall()
    for row in rows:
        dbuid = row[1]
        dbpw = row[2]
        dbstate = row[3]
        if (tempuid == dbuid and temppw == dbpw and dbstate == "offline"):
            print(tempuid, "connected!")
            state = "authenticated"
            cur.execute("UPDATE LOGIN SET state = '" + tempstate + "' WHERE userid = '" + dbuid + "';")
            conn.commit()
            app.savevariable("userid", tempuid, c)
        elif (tempuid == dbuid and temppw == dbpw and dbstate != "offline"):
            state = "duplicate"
            break
        elif (tempuid == dbuid and temppw != dbpw):
            state = "password"
    else:
        if (dbuid is None):
            state = "userid"
    app.emit("login", {'state':state, 'userid':tempuid,}, c)
    conn.close()

@app.channel("connect")
def connect(c,addr):
    global iden
    app.savevariable("id", iden, c)
    iden+= 1
    
@app.channel("disconnect")
def disconnect(c, addr):
    conn = psycopg2.connect(database = "logindb", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5432")
    cur = conn.cursor()
    userid = app.callvariable("userid", c)
    if (userid != None):
        cur.execute("UPDATE LOGIN SET state = 'offline' WHERE userid = '" + userid + "';")
        conn.commit()
        cur.execute("UPDATE LOGIN SET party_info = '' WHERE userid = '" + userid + "';")
        conn.commit()
        print(userid + " has disconnected!")
        conn.close()
 

@app.channel("chat")
def chat(c, addr, data):
    print(data['userid'] + ": " + data['message'])
    app.broadcast("chat", {'userid':data['userid'], 'message':data['message']})

@app.channel("tell")
def tell(c, addr, data):
    target = app.callvariablelist("userid", data['target'])
    if target:
        app.emit("tell", {'userid':data['userid'], 'target':data['target'], 'message':data['message']}, target[0])
    else:
        app.emit("tell", {'userid':data['userid'], 'target':'System', 'message':"ERROR: User not found online!"}, c)

@app.channel("move")
def chat(c, addr, data):
    print(str(data['userid']) + " " + str(data['x_move']) + " " + str(data['y_move']))
    app.broadcast("move", {'userid':data['userid'], 'x_move':data['x_move'], 'y_move':data['y_move']})

@app.channel("users")
def users(c, addr, data):    
    conn = psycopg2.connect(database = "logindb", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5432")
    cur = conn.cursor()
    cur.execute("SELECT id, userid from LOGIN WHERE state != 'offline'")
    online = cur.fetchall()
    qsize = len(online)
    for i in online:
        app.broadcast("users", {'id':i[0], 'userid':i[1]})
    conn.close()

@app.channel("party")
def users(c, addr, data):
    conn = psycopg2.connect(database = "logindb", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5432")
    cur = conn.cursor()
    if data['type'] == "invitation":
        cur.execute("SELECT id, party_info from LOGIN WHERE state != 'offline' and userid = '" + data['target'] +"'")
        online = cur.fetchall()
        target = app.callvariablelist("userid", data['target'])
        if online:
            party = online[0][1]
            if party == '':
                app.emit("party", {'userid':data['userid'], 'type':'invite'},target[0]);
    elif data['type'] == "join":
        print(data['userid'] + " joined the party!")
        cur.execute("UPDATE LOGIN SET party_info = '" + data['target'] + "' WHERE userid = '" + data['userid'] + "';")
        conn.commit()
        cur.execute("UPDATE LOGIN SET party_info = '" + data['target'] + "' WHERE userid = '" + data['target'] + "';")
        conn.commit()
    conn.close()
 
@app.channel("inventory")
def inventory(c, addr, data):
    userid = data['userid']
    request_type = data['request']
    conn = psycopg2.connect(database = "logindb", user = "postgres", password = "postgres", host = "127.0.0.1", port = "5432")
    print("Opened database successfully")
    cur = conn.cursor()
    if (request_type == "get_inv"):
        cur.execute("SELECT items.item_id, inventory.quantity FROM login JOIN inventory ON login.id = inventory.player_id JOIN items ON inventory.item_id = items.item_id WHERE userid = '" + userid + "'")
        items = cur.fetchall()
        for item in items:
            app.emit("inventory", {'item_id':item[0], 'item_quantity':item[1]}, c)
    conn.close()
    
app.server("127.0.0.1", 5000)
