import logging
import sqlite3

logger = logging.getLogger("caas.database")


def connect():
    try:
        # FIXME: use environment variables for database path
        con = sqlite3.connect("data/caas.db")
        cur = con.cursor()
        return (con, cur)
    except sqlite3.Error as e:
        logger.error("Error connecting to database")
        logger.debug(e)
        return None, None


def release(con):
    try:
        if con:
            con.commit()
            con.close()
    except sqlite3.Error as e:
        logger.error("Error releasing database connection")
        logger.debug(e)


def select_user(token):
    try:
        (con, cur) = connect()
        res = cur.execute(
            "SELECT username, token, salted_secret_hash FROM users WHERE token = ?",
            (token,),
        )
        row = res.fetchone()
        release(con)
        return row
    except sqlite3.Error as e:
        logger.error("Error selecting user")
        logger.debug(e)
        return None


def insert_new_user(username, pt, token, salted_secret_hash, timestamp):
    try:
        (con, cur) = connect()
        cur.execute(
            "INSERT INTO users (username, pt, token, salted_secret_hash, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, pt, token, salted_secret_hash, timestamp),
        )
        release(con)
    except sqlite3.Error as e:
        logger.error("Error inserting new user")
        logger.debug(e)
