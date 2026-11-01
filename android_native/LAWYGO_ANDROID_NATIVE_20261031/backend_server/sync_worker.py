"""Cron/Task Scheduler worker: sync consented owned Google channels every 6 hours.
Usage: python sync_worker.py --once  |  python sync_worker.py --loop
Run only one scheduler process per SQLite database. Backups and external DB required for HA.
"""
import argparse, time, traceback
from datetime import datetime, timezone
import app
import integrations_v2

INTERVAL_SEC=6*3600

def sync_once():
    app.init_db()
    counts={'sources':0,'created':0,'updated':0,'errors':0}
    with app.connect() as db:
        rows=db.execute('SELECT * FROM sync_sources ORDER BY created_at').fetchall()
        for row in rows:
            # Only sources with matching per-user OAuth authorization can sync.
            if row['last_sync_at']:
                try:
                    if (datetime.now(timezone.utc)-datetime.fromisoformat(row['last_sync_at'])).total_seconds()<INTERVAL_SEC:
                        continue
                except ValueError:pass
            counts['sources']+=1
            try:
                with app.transaction(db):
                    result=integrations_v2._sync_source(db,row)
                counts['created']+=result['created'];counts['updated']+=result['updated']
            except Exception as e:
                counts['errors']+=1
                db.execute('INSERT INTO sync_runs(id,source_id,status,created_at,error) VALUES(?,?,?,?,?)',(
                    __import__('uuid').uuid4().hex,row['id'],'error',app.now(),type(e).__name__))
    return counts

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--loop',action='store_true');a.add_argument('--once',action='store_true');args=a.parse_args()
    while True:
        print('LAWYGO Google sync',sync_once(),flush=True)
        if not args.loop:break
        time.sleep(3600)
