#!/usr/bin/env python3

import sqlite3
import config

conn = sqlite3.connect(config.USERS_DB_PATH)
conn.cursor().execute('''CREATE TABLE IF NOT EXISTS users(
                            id  INTEGER PRIMARY KEY,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            reg_time TEXT UNIQUE NOT NULL,
                            last_login TEXT
                        )''')

conn.cursor().execute('''CREATE TABLE IF NOT EXISTS messages(
                            id  INTEGER PRIMARY KEY,
                            src TEXT NOT NULL,
                            dest TEXT NOT NULL,
                            time TEXT NOT NULL,
                            msg TEXT NOT NULL
                        )''')
conn.commit()
