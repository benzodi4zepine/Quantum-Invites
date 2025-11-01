import sqlite3
from sqlite3 import Error

from app.bot.helper.dbupdater import check_table_version, update_table

DB_URL = 'app/config/app.db'
DB_TABLE = 'clients'

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print("Connected to db")
    except Error as e:
        print("error in connecting to db")
    finally:
        if conn:
            return conn

def checkTableExists(dbcon, tablename):
    dbcur = dbcon.cursor()
    dbcur.execute("""SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{0}';""".format(tablename.replace('\'', '\'\'')))
    if dbcur.fetchone()[0] == 1:
        dbcur.close()
        return True
    dbcur.close()
    return False

conn = create_connection(DB_URL)

# Checking if table exists
if checkTableExists(conn, DB_TABLE):
	print('Table exists.')
else:
    conn.execute(
    '''CREATE TABLE "clients" (
    "id"	INTEGER NOT NULL UNIQUE,
    "discord_username"	TEXT NOT NULL UNIQUE,
    "email"	TEXT,
    "jellyfin_username"	TEXT,
    "emby_username"	TEXT,
    "subscription_expires_at"	TEXT,
    "subscription_last_reminder_at"	TEXT,
    "subscription_reminder_flags"	TEXT,
    PRIMARY KEY("id" AUTOINCREMENT)
    );''')

update_table(conn, DB_TABLE)

def save_user_email(username, email):
    if not username or not email:
        return "Username and email cannot be empty"

    conn.execute(
        """
        INSERT INTO clients(discord_username, email)
        VALUES(?, ?)
        ON CONFLICT(discord_username) DO UPDATE SET email=excluded.email
        """,
        (username, email),
    )
    conn.commit()
    print("User email saved to db.")


def save_user(username):
    if not username:
        return "Username cannot be empty"

    conn.execute(
        """
        INSERT INTO clients(discord_username)
        VALUES(?)
        ON CONFLICT(discord_username) DO NOTHING
        """,
        (username,),
    )
    conn.commit()
    print("User added to db.")


def save_user_jellyfin(username, jellyfin_username):
    if not username or not jellyfin_username:
        return "Discord and Jellyfin usernames cannot be empty"

    conn.execute(
        """
        INSERT INTO clients(discord_username, jellyfin_username)
        VALUES(?, ?)
        ON CONFLICT(discord_username) DO UPDATE SET jellyfin_username=excluded.jellyfin_username
        """,
        (username, jellyfin_username),
    )
    conn.commit()
    print("User jellyfin username saved to db.")


def save_user_emby(username, emby_username):
    if not username or not emby_username:
        return "Discord and Emby usernames cannot be empty"

    conn.execute(
        """
        INSERT INTO clients(discord_username, emby_username)
        VALUES(?, ?)
        ON CONFLICT(discord_username) DO UPDATE SET emby_username=excluded.emby_username
        """,
        (username, emby_username),
    )
    conn.commit()
    print("User emby username saved to db.")


def save_user_all(
    username,
    email=None,
    jellyfin_username=None,
    emby_username=None,
    subscription_expires_at=None,
    subscription_last_reminder_at=None,
    subscription_reminder_flags=None
):
    if not username:
        return "Discord username must be provided"

    update_fields = []
    params = [username]
    columns = ["discord_username"]
    placeholders = ["?"]

    for column, value in (
        ("email", email),
        ("jellyfin_username", jellyfin_username),
        ("emby_username", emby_username),
        ("subscription_expires_at", subscription_expires_at),
        ("subscription_last_reminder_at", subscription_last_reminder_at),
        ("subscription_reminder_flags", subscription_reminder_flags),
    ):
        if value is not None and value != "":
            columns.append(column)
            placeholders.append("?")
            params.append(value)
            update_fields.append(f"{column}=excluded.{column}")

    if len(columns) == 1:
        return save_user(username)

    query = f"""
        INSERT INTO clients({", ".join(columns)})
        VALUES({", ".join(placeholders)})
        ON CONFLICT(discord_username) DO UPDATE SET {", ".join(update_fields)}
    """
    conn.execute(query, tuple(params))
    conn.commit()
    print("User information saved to db.")


def get_useremail(username):
    if not username:
        return "username cannot be empty"

    try:
        cursor = conn.execute(
            "SELECT email FROM clients WHERE discord_username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return "No email found"
    except Error:
        return "error in fetching from db"


def get_jellyfin_username(username):
    if not username:
        return "username cannot be empty"

    try:
        cursor = conn.execute(
            "SELECT jellyfin_username FROM clients WHERE discord_username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return "No users found"
    except Error:
        return "error in fetching from db"


def get_emby_username(username):
    if not username:
        return "username cannot be empty"

    try:
        cursor = conn.execute(
            "SELECT emby_username FROM clients WHERE discord_username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return "No users found"
    except Error:
        return "error in fetching from db"


def remove_email(username):
    if not username:
        print("Username cannot be empty.")
        return False

    conn.execute(
        "UPDATE clients SET email = NULL WHERE discord_username = ?",
        (username,),
    )
    conn.commit()
    print(f"Email removed from user {username} in database")
    return True


def remove_jellyfin(username):
    if not username:
        print("Username cannot be empty.")
        return False

    conn.execute(
        "UPDATE clients SET jellyfin_username = NULL WHERE discord_username = ?",
        (username,),
    )
    conn.commit()
    print(f"Jellyfin username removed from user {username} in database")
    return True


def remove_emby(username):
    if not username:
        print("Username cannot be empty.")
        return False

    conn.execute(
        "UPDATE clients SET emby_username = NULL WHERE discord_username = ?",
        (username,),
    )
    conn.commit()
    print(f"Emby username removed from user {username} in database")
    return True


def get_subscription(username):
    if not username:
        return None

    cursor = conn.execute(
        """
        SELECT subscription_expires_at, subscription_last_reminder_at, subscription_reminder_flags
        FROM clients WHERE discord_username = ?
        """,
        (username,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "expires_at": row[0],
        "last_reminder_at": row[1],
        "reminder_flags": row[2] or ""
    }


def set_subscription(username, expires_at, reset_flags=True):
    if not username:
        return False

    save_user(username)
    current = get_subscription(username)
    reminder_flags = ""
    if not reset_flags and current and current.get("reminder_flags"):
        reminder_flags = current["reminder_flags"]

    conn.execute(
        """
        UPDATE clients
        SET subscription_expires_at = ?,
            subscription_last_reminder_at = NULL,
            subscription_reminder_flags = ?
        WHERE discord_username = ?
        """,
        (expires_at, reminder_flags, username),
    )
    conn.commit()
    return True


def clear_subscription(username):
    if not username:
        return False

    conn.execute(
        """
        UPDATE clients
        SET subscription_expires_at = NULL,
            subscription_last_reminder_at = NULL,
            subscription_reminder_flags = NULL
        WHERE discord_username = ?
        """,
        (username,),
    )
    conn.commit()
    return True


def list_subscriptions():
    cursor = conn.execute(
        """
        SELECT discord_username, subscription_expires_at,
               subscription_last_reminder_at, subscription_reminder_flags
        FROM clients
        WHERE subscription_expires_at IS NOT NULL
        """
    )
    rows = cursor.fetchall()
    subscriptions = []
    for row in rows:
        subscriptions.append({
            "discord_username": row[0],
            "expires_at": row[1],
            "last_reminder_at": row[2],
            "reminder_flags": row[3] or ""
        })
    return subscriptions


def mark_reminder_sent(username, reminder_code, reminder_time):
    if not username:
        return False

    info = get_subscription(username) or {"reminder_flags": ""}
    flags = set()
    if info["reminder_flags"]:
        flags.update({flag.strip() for flag in info["reminder_flags"].split(',') if flag.strip()})
    flags.add(str(reminder_code))

    def sort_key(value):
        if value.lstrip('-').isdigit():
            return (0, -int(value))
        return (1, value)

    conn.execute(
        """
        UPDATE clients
        SET subscription_last_reminder_at = ?,
            subscription_reminder_flags = ?
        WHERE discord_username = ?
        """,
        (reminder_time, ",".join(sorted(flags, key=sort_key)), username),
    )
    conn.commit()
    return True


def delete_user(username):
    if not username:
        return "username cannot be empty"

    try:
        conn.execute(
            "DELETE FROM clients WHERE discord_username = ?",
            (username,),
        )
        conn.commit()
        return True
    except Error:
        return False


def read_all():
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients")
    rows = cur.fetchall()
    all = []
    for row in rows:
        all.append(row)
    return all
