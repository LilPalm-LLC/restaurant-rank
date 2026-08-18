import tempfile
from pathlib import Path
import services.storage as storage

def test_storage_profile_and_favorites(tmp_path):
    old=storage.DB_PATH; storage.DB_PATH=Path(tmp_path)/'db.sqlite3'
    try:
        pid=storage.create_profile('Test','1234','ABCD-2345-EFGH')
        assert storage.get_profile(pid)['name']=='Test'
        cols=storage.collections(pid); assert cols
        storage.save_favorite(pid,cols[0]['id'],'place1',{'place_id':'place1','name':'Test Restaurant'})
        assert len(storage.favorite_rows(pid))==1
        data=storage.export_backup(pid); assert data['format']=='restaurant-rank-backup'
    finally: storage.DB_PATH=old
