# Supplemental auth checks isolated from production DB; pytest loads from test_engine fixture module.
from test_engine import c,auth,post

def test_trash_and_board_trash(c):
    h=auth(c,'admin')
    p=post(c,'channel',h)
    assert p.status_code==201
    pid=p.json()['id']
    assert c.delete('/api/posts/'+pid,headers=h).status_code==200
    assert any(x['id']==pid for x in c.get('/api/trash').json()['items'])
    assert c.post('/api/posts/'+pid+'/restore',headers=h).status_code==200
    assert all(x['id']!=pid for x in c.get('/api/trash').json()['items'])

def test_no_private_other_article_in_admin_list(c):
    h=auth(c,'contributor')
    p=post(c,'pan',h,visibility='private')
    assert p.status_code==201
    pid=p.json()['id']
    auth(c,'admin')
    assert not any(x['id']==pid for x in c.get('/api/posts').json()['items'])
    assert c.get('/api/posts/'+pid).status_code==404
