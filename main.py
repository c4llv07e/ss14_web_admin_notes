#!/usr/bin/env python3
import json
from flask import request, Flask, abort, jsonify, render_template
import psycopg2
import os
import sys
import time

class Note:
    def __init__(self, id, round, player_id, player_name, message, admin_id,
                 admin_name, created_time, last_edited_by_id,
                 last_edited_by_name, is_deleted, deleted_by_id,
                 deleted_by_name, deleted_time, is_secret, expiration_time,
                 severity):
        self.id = id
        self.round = round
        self.player_id = player_id
        self.player_name = player_name
        self.message = message
        self.admin_id = admin_id
        self.admin_name = admin_name
        self.created_time = created_time
        self.last_edited_by_id = last_edited_by_id
        self.last_edited_by_name = last_edited_by_name
        self.is_deleted = is_deleted
        self.deleted_by_id = deleted_by_id
        self.deleted_by_name = deleted_by_name
        self.deleted_time = deleted_time
        self.is_secret = is_secret
        self.expiration_time = expiration_time
        self.severity = severity
        pass
    def to_list(self):
        return {
            "id": self.id,
            "round": self.round,
            "player_id": self.player_id,
            "player_name": self.player_name,
            "message": self.message,
            "admin_id": self.admin_id,
            "admin_name": self.admin_name,
            "created_time": self.created_time.isoformat(),
            "last_edited_by_id": self.last_edited_by_id,
            "last_edited_by_name": self.last_edited_by_name,
            "is_deleted": self.is_deleted,
            "deleted_by_id": self.deleted_by_id,
            "deleted_by_name": self.deleted_by_name,
            "deleted_time": (self.deleted_time.isoformat() if
                             self.is_deleted else None),
            "is_secret": self.is_secret,
            "expiration_time": (self.expiration_time.isoformat() if
                                self.expiration_time else None),
            "severity": self.severity,
        }
    pass

host_env_name = "POSTGRES_HOST"
user_env_name = "POSTGRES_USER"
db_env_name = "POSTGRES_DATABASE"
password_env_name = "POSTGRES_PASSWORD"
server_name_env_name = "SS14_SERVER_NAME"

server_name = os.getenv(server_name_env_name, "Adventure space")

app = Flask(__name__)
db = None

def eprint(*args, **kwargs):
    return print(*args, file=sys.stderr, **kwargs)

def get_notes():
    if db == None:
        return None, "db isn't connected"
    cur = db.cursor()
    cur.execute("""
SELECT
  an.admin_notes_id,
  an.round_id,
  an.player_user_id,
  pp.last_seen_user_name,
  an.message,
  an.created_by_id,
  pa.last_seen_user_name,
  an.created_at,
  an.last_edited_by_id,
  pe.last_seen_user_name,
  an.deleted,
  an.deleted_by_id,
  pd.last_seen_user_name,
  an.deleted_at,
  an.secret,
  an.expiration_time,
  an.severity
FROM admin_notes an
  LEFT JOIN player pp ON (an.player_user_id = pp.user_id)
  LEFT JOIN player pa ON (an.created_by_id = pa.user_id)
  LEFT JOIN player pe ON (an.last_edited_by_id = pe.user_id)
  LEFT JOIN player pd ON (an.deleted_by_id = pd.user_id)
ORDER BY an.created_at DESC;
""")
    notes = list()
    while (note_raw := cur.fetchone()) != None:
        (note_id, round_id,
         player_id, player_name,
         message, admin_id,
         admin_name, created_at,
         last_edited_id, last_edited_name,
         is_deleted, deleted_by_id,
         deleted_by_name, deleted_at,
         is_secret, expiration_time,
         severity
         ) = note_raw
        note = Note(note_id, round_id, player_id, player_name,
                    message, admin_id, admin_name, created_at, last_edited_id,
                    last_edited_name, is_deleted, deleted_by_id,
                    deleted_by_name, deleted_at, is_secret, expiration_time,
                    severity)
        notes.append(note)
        pass
    cur.close()
    return notes, None

@app.route("/admin_notes.json", methods=["GET"])
def route_admin_notes():
    # Almost golang
    notes, err = get_notes()
    if err != None:
        return err, 500
    return json.dumps(list(map(lambda x: x.to_list(), notes)))

@app.route("/", methods=["GET"])
def route_root():
    notes, err = get_notes()
    if err != None:
        return err, 500
    return render_template("index.html", server_name=server_name, notes=notes)

def get_env_or_exit(env):
    if env not in os.environ:
        eprint(f"Error, {env} is unset")
        sys.exit(-1)
    return os.environ[env]

def db_init():
    global db
    db_host = os.getenv(host_env_name, "localhost")
    db_password = os.getenv(password_env_name, "None")
    db_user = os.getenv(user_env_name, "ss14")
    db_name = os.getenv(db_env_name, "ss14")
    db = psycopg2.connect(host=db_host, database=db_name, user=db_user,
                          password=db_password)
    pass

if __name__ == '__main__':
    db_init()
    debug = "DEV_MODE" in os.environ
    app.run(host="0.0.0.0", port="3411", debug=debug)
    pass

