"""Invoke every day at 07:10 Asia/Seoul via Task Scheduler or cron; no SMTP send."""
import json
from app import init_db,connect
from editorial_v5 import collect,create_draft,today_kst,enhance_draft_ai
import os
init_db()
with connect() as db:
    fetches=collect(db)
    draft=create_draft(db)
    ai_status='disabled'
    if os.getenv('LAWYGO_EDITORIAL_AI_ENABLED','').lower()=='true' and os.getenv('GEMINI_API_KEY') and draft['generator']=='rule-based':
        try:
            draft=enhance_draft_ai(db,draft['id']);ai_status='generated'
        except Exception as e:
            ai_status=type(e).__name__ + ': fallback rule-based draft preserved'
    print(json.dumps({'issue_day':today_kst(),'sources':fetches,'draft_id':draft['id'],'new_items':sum(x['added'] for x in fetches),'sent_emails':0,'ai_status':ai_status},ensure_ascii=False,indent=2))
