"""Consistent SQLite backup with a manifest, including uploaded media; local only."""
from pathlib import Path
import argparse,datetime,json,shutil,sqlite3,zipfile,hashlib,os
p=argparse.ArgumentParser();p.add_argument('--root',required=True);ns=p.parse_args()
root=Path(ns.root).resolve();db=root/'data'/'lawygo.db'
if not db.exists():raise SystemExit('No existing user database to back up.')
backup=root/'backups';backup.mkdir(parents=True,exist_ok=True)
date=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
file=backup/('LAWYGO_BACKUP_'+date+'.zip')
# SQLite online backup works while server is running.
tmp=backup/('backup_'+date+'.sqlite')
try:
    with sqlite3.connect(db) as source,sqlite3.connect(tmp) as target:
        source.backup(target)
    with zipfile.ZipFile(file,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(tmp,'data/lawygo.db')
        for img in sorted((root/'data'/'uploads').rglob('*')) if (root/'data'/'uploads').exists() else []:
            if img.is_file():z.write(img,'data/uploads/'+str(img.relative_to(root/'data'/'uploads')).replace(os.sep,'/'))
        z.writestr('BACKUP_INFO.json',json.dumps({'timestamp':date,'notes':'Sensitive user information. Do not publish this backup.'},ensure_ascii=False))
finally:tmp.unlink(missing_ok=True)
print('Backup saved:',file)
