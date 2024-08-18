import sqlite3
import hashlib
con=sqlite3.connect("userdata.db")
cur=con.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS userdata (
    client_id,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL
)
""")
username1, password1="hozan",hashlib.sha256("hozanpassword".encode()).hexdigest()
username2, password2="xalid",hashlib.sha256("xalidpassword".encode()).hexdigest()
username3, password3="mo",hashlib.sha256("mopassword".encode()).hexdigest()
username4, password4="ali",hashlib.sha256("alipassword".encode()).hexdigest()
cur.execute("INSERT INTO userdata (username,password) VALUES (?, ?)",(username1,password1))
cur.execute("INSERT INTO userdata (username,password) VALUES (?, ?)",(username2,password2))
cur.execute("INSERT INTO userdata (username,password) VALUES (?, ?)",(username3,password3))
cur.execute("INSERT INTO userdata (username,password) VALUES (?, ?)",(username4,password4))

con.commit()