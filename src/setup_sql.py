#!/usr/bin/env python3

import sqlite3

conn = sqlite3.connect("./users.db")
conn.cursor().execute('''CREATE TABLE IF NOT EXISTS users(
                            id  INTEGER PRIMARY KEY,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            reg_time TEXT UNIQUE NOT NULL,
                            last_login TEXT
                        )''')

conn.commit()
