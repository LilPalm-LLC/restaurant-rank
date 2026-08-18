import json, os, sqlite3, time
from pathlib import Path
from contextlib import contextmanager
from uuid import uuid4
from models.profile import UserSettings
from utils.security import hash_secret, verify_secret, now_utc_iso, normalize_recovery_code

DB_PATH = Path(os.environ.get("RESTAURANTRANK_DB_PATH", Path.cwd() / "restaurant_rank.sqlite3"))

@contextmanager
def db():
    conn=sqlite3.connect(DB_PATH)
    conn.row_factory=sqlite3.Row
    try:
        init_db(conn)
        yield conn
        conn.commit()
    finally: conn.close()

def init_db(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY,name TEXT NOT NULL,pin_hash TEXT NOT NULL,recovery_hash TEXT NOT NULL,created_at TEXT NOT NULL,language TEXT NOT NULL DEFAULT 'en',distance_unit TEXT NOT NULL DEFAULT 'auto',default_radius INTEGER NOT NULL DEFAULT 5,theme TEXT NOT NULL DEFAULT 'ocean',appearance TEXT NOT NULL DEFAULT 'system',failed_attempts INTEGER NOT NULL DEFAULT 0,locked_until INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS collections (id TEXT PRIMARY KEY,profile_id TEXT NOT NULL,name TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(profile_id,name),FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS favorites (profile_id TEXT NOT NULL,collection_id TEXT NOT NULL,place_id TEXT NOT NULL,payload TEXT NOT NULL,saved_at TEXT NOT NULL,PRIMARY KEY(collection_id,place_id),FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE,FOREIGN KEY(collection_id) REFERENCES collections(id) ON DELETE CASCADE);
    ''')

def create_profile(name:str,pin:str,recovery_code:str):
    pid=str(uuid4()); now=now_utc_iso()
    with db() as c:
        c.execute("INSERT INTO profiles VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(pid,name,hash_secret(pin),hash_secret(normalize_recovery_code(recovery_code)),now,"en","auto",5,"ocean","system",0,0))
        cid=str(uuid4()); c.execute("INSERT INTO collections VALUES (?,?,?,?)",(cid,pid,"My Favorites",now))
    return pid

def list_profiles():
    with db() as c: return c.execute("SELECT id,name,created_at FROM profiles ORDER BY name COLLATE NOCASE").fetchall()

def get_profile(pid):
    with db() as c: return c.execute("SELECT * FROM profiles WHERE id=?",(pid,)).fetchone()

def authenticate_pin(pid,pin):
    now=int(time.time())
    with db() as c:
        row=c.execute("SELECT * FROM profiles WHERE id=?",(pid,)).fetchone()
        if not row: return False,"not_found"
        if row["locked_until"]>now: return False,"locked"
        if verify_secret(pin,row["pin_hash"]):
            c.execute("UPDATE profiles SET failed_attempts=0,locked_until=0 WHERE id=?",(pid,)); return True,"ok"
        attempts=row["failed_attempts"]+1
        cooldown=min(300,2**min(attempts,7)) if attempts>=3 else 0
        c.execute("UPDATE profiles SET failed_attempts=?,locked_until=? WHERE id=?",(attempts,now+cooldown,pid)); return False,"wrong"

def authenticate_recovery(pid,code):
    row=get_profile(pid)
    return bool(row and verify_secret(normalize_recovery_code(code),row["recovery_hash"]))

def change_pin(pid,new_pin):
    with db() as c: c.execute("UPDATE profiles SET pin_hash=?,failed_attempts=0,locked_until=0 WHERE id=?",(hash_secret(new_pin),pid))

def update_settings(pid,**kwargs):
    allowed={k:v for k,v in kwargs.items() if k in {"language","distance_unit","default_radius","theme","appearance"}}
    if not allowed:return
    sets=",".join(f"{k}=?" for k in allowed)
    with db() as c:c.execute(f"UPDATE profiles SET {sets} WHERE id=?",(*allowed.values(),pid))

def create_collection(pid,name):
    cid=str(uuid4())
    with db() as c: c.execute("INSERT INTO collections VALUES (?,?,?,?,?)",(cid,pid,name,now_utc_iso()))
    return cid

def collections(pid):
    with db() as c:return c.execute("SELECT * FROM collections WHERE profile_id=? ORDER BY name COLLATE NOCASE",(pid,)).fetchall()

def rename_collection(pid,cid,name):
    with db() as c:c.execute("UPDATE collections SET name=? WHERE id=? AND profile_id=?",(name,cid,pid))

def delete_collection(pid,cid):
    with db() as c:
        c.execute("DELETE FROM favorites WHERE collection_id=? AND profile_id=?",(cid,pid)); c.execute("DELETE FROM collections WHERE id=? AND profile_id=?",(cid,pid))

def save_favorite(pid,cid,place_id,payload):
    with db() as c:
        c.execute("INSERT OR IGNORE INTO favorites VALUES (?,?,?,?,?)",(pid,cid,place_id,json.dumps(payload,ensure_ascii=False),now_utc_iso()))

def remove_favorite(pid,cid,place_id):
    with db() as c:c.execute("DELETE FROM favorites WHERE profile_id=? AND collection_id=? AND place_id=?",(pid,cid,place_id))

def favorite_rows(pid,cid=None):
    with db() as c:
        q="SELECT f.*,c.name collection_name FROM favorites f JOIN collections c ON f.collection_id=c.id WHERE f.profile_id=?"; args=[pid]
        if cid:q+=" AND f.collection_id=?"; args.append(cid)
        return c.execute(q,args).fetchall()

def export_backup(pid):
    p=get_profile(pid); cols=collections(pid); fav=favorite_rows(pid)
    return {"format":"restaurant-rank-backup","version":1,"created_at":now_utc_iso(),"profile":{"name":p["name"]},"settings":{"language":p["language"],"distance_unit":p["distance_unit"],"default_radius":p["default_radius"],"theme":p["theme"],"appearance":p["appearance"]},"favorite_lists":[{"name":c["name"],"created_at":c["created_at"],"restaurants":[json.loads(f["payload"])|{"saved_at":f["saved_at"]} for f in fav if f["collection_id"]==c["id"]]} for c in cols]}

def import_backup(pid,obj,mode="merge"):
    cols=collections(pid); existing={c["name"]:c["id"] for c in cols}
    if mode=="replace":
        with db() as c:
            c.execute("DELETE FROM favorites WHERE profile_id=?",(pid,)); c.execute("DELETE FROM collections WHERE profile_id=?",(pid,))
        existing={}
    for item in obj["favorite_lists"]:
        name=str(item.get("name") or "Imported")[:60]
        cid=existing.get(name) or create_collection(pid,name); existing[name]=cid
        for r in item.get("restaurants",[]):
            place_id=r.get("place_id")
            if place_id: save_favorite(pid,cid,place_id,r)
    update_settings(pid,**obj.get("settings",{}))

def delete_profile(pid):
    with db() as c:c.execute("DELETE FROM profiles WHERE id=?",(pid,))
