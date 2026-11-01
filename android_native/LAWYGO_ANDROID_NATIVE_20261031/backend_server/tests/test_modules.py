from test_engine import c,auth,post

def test_wiki_public_search(c):
    h=auth(c,'editor')
    created=post(c,'wiki',h,status='published',title='공시송달 실무 검토',body='공시송달과 기간의 관계를 출처와 함께 설명합니다.')
    assert created.status_code==201
    c.cookies.clear()
    data=c.get('/api/wiki/search?q=공시송달').json()
    assert any(x['title']=='공시송달 실무 검토' for x in data['items'])


def test_note_extractive_summary_privacy(c):
    h=auth(c,'contributor')
    created=post(c,'note',h,body='계약 위반에 따른 지급 통지와 보증 문제입니다. 해당 법률 절차를 확인해야 합니다.')
    assert created.status_code==201
    pid=created.json()['id']
    data=c.get('/api/note/'+pid+'/extract').json()
    assert data['post_id']==pid
    assert 'AI 법률판단' in data['notice']
    auth(c,'other')
    assert c.get('/api/note/'+pid+'/extract').status_code==404


def test_pan_private_inquiry(c):
    h=auth(c,'editor')
    profile=c.post('/api/posts',headers=h,json={'board_id':c.get('/api/boards?product=pan').json()['items'][0]['id'],'kind':'profile','title':'가상 변호사 프로필','body':'실제 변호사 등록 시 인증 필요.','status':'published','visibility':'public'})
    assert profile.status_code==201
    pid=profile.json()['id']
    h=auth(c,'contributor')
    assert c.post('/api/pan/inquiries',headers=h,json={'profile_post_id':pid,'message':'상담 문의 내용은 10자 이상입니다.','privacy_consent':False}).status_code==400
    r=c.post('/api/pan/inquiries',headers=h,json={'profile_post_id':pid,'message':'상담 문의 내용은 10자 이상입니다.','privacy_consent':True})
    assert r.status_code==201,r.text
    assert len(c.get('/api/pan/inquiries').json()['items'])==0
    auth(c,'editor')
    inbox=c.get('/api/pan/inquiries').json()
    assert len(inbox['items'])>=1
    assert inbox['items'][0]['body']=='상담 문의 내용은 10자 이상입니다.'
