from pathlib import Path
p=Path('/mnt/data/LAWYGO_PAN_2026_EXPANSION/backend/app.py')
s=p.read_text()
start=s.index('# Static files mounted last:')
s=s[:start]+'''
@app.get('/api/feed')
async def approved_feed(kind:str='all'):
    if kind not in ('all','blog','video'):
        raise HTTPException(400,'올바르지 않은 콘텐츠 유형입니다.')
    with database() as db:
        rows=db.execute('SELECT id,content_type,title,url,summary,created_at FROM content_submissions WHERE approved=1 AND (?=\"all\" OR content_type=?) ORDER BY id DESC LIMIT 50',(kind,kind)).fetchall()
    return {'contents':[dict(row) for row in rows]}

@app.post('/api/inquiry')
async def submit_inquiry(request:Request):
    throttled(request,'inquiry',6)
    d=await request.json()
    if not d.get('consent'):raise HTTPException(400,'상담정보 전송에 대한 동의가 필요합니다.')
    slug=str(d.get('profile','')).strip()[:60]
    if not re.fullmatch(r'[a-z0-9-]{3,60}',slug):raise HTTPException(400,'프로필 주소가 올바르지 않습니다.')
    name=str(d.get('name','')).strip()[:60]
    email=validate_email(d.get('email',''))
    message=str(d.get('message','')).strip()
    method=d.get('method','email')
    if method not in ('email','callback') or len(name)<2 or not (10<=len(message)<=1500):
        raise HTTPException(400,'신청 내용을 확인해 주세요.')
    check_mail_ready()
    with database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS profile_routes (slug TEXT PRIMARY KEY,member_email TEXT NOT NULL,activated INTEGER DEFAULT 0)')
        profile=db.execute('SELECT member_email FROM profile_routes WHERE slug=? AND activated=1',(slug,)).fetchone()
        if not profile:raise HTTPException(409,'이 프로필의 연결 계정은 아직 운영 인증되지 않았습니다.')
        dest=profile['member_email']
        db.execute('INSERT INTO inquiries(lawyer_id,contact_method,name,email,message,created_at,consent) VALUES (?,?,?,?,?,?,1)',(slug,method,name,email,message,now()))
        db.commit()
    mail(dest,'[LAWYGO PAN] 새로운 비공개 상담 연결 요청',f'프로필: {slug}\\n문의 방법: {method}\\n신청자: {name}\\n회신 이메일: {email}\\n요약: {message}\\n\\n민감정보는 필요 최소한으로 다뤄 주세요.')
    return {'message':'인증된 변호사 계정으로 비공개 요청이 전달되었습니다. 실제 상담 수임은 별도 계약에 따릅니다.'}

'''+s[start:]
p.write_text(s)
