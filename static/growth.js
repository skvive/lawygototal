/* LAWYGO v3 operations: DOM-safe rendering, mouse drag-and-drop AND keyboard ordering. */
const growthText=(t,v,c='')=>{const n=document.createElement(t);n.textContent=String(v??'');if(c)n.className=c;return n};
const growthBtn=(label,callback,cls='btn small secondary')=>{let b=growthText('button',label,cls);b.type='button';b.addEventListener('click',callback);return b};
let growthCampaigns=[],growthOrdering=[],boardOrdering=[];
function gErr(e){display(e?.message||'기능을 처리하지 못했습니다.',true)}
async function loadGrowth(){
  if(!me){$('growthBody').replaceChildren(growthText('p','로그인이 필요합니다.','error'));return}
  try{
    const panDash=await request('/api/growth/pan-dashboard').catch(()=>null);
    const panEl=$('panMemberDashboard');
    if(panDash&&panEl){
      panEl.classList.remove('hidden');
      $('panDashMonth').textContent=panDash.month;
      $('panDashDisclaimer').textContent=panDash.disclaimer;
      const f=panDash.funnel||{};
      $('panImp').textContent=f.impression||0;
      $('panContentOpen').textContent=f.content_open||0;
      $('panProfileOpen').textContent=f.profile_open||0;
      $('panConsultClick').textContent=f.consult_click||0;
      $('panInquiries').textContent=panDash.inquiries_received||0;
    }else if(panEl)panEl.classList.add('hidden');
    if(!['admin','editor'].includes(me.role)){
      $('growthBody').replaceChildren(growthText('p','운영 캠페인·심사는 admin/editor 전용입니다. 위 PAN 성장 지표는 본인 콘텐츠 기준입니다.','muted'));
      return;
    }
    const [campaigns,analytic,system,verification,entitlements]=await Promise.all([
      request('/api/growth/campaigns'),request('/api/growth/analytics'),request('/api/growth/system'),
      request('/api/pan/verification'),request('/api/growth/entitlements')]);
    growthCampaigns=campaigns.items;
    $('growthAds').textContent=growthCampaigns.length;
    const totals=analytic.totals||{};
    $('growthViews').textContent=totals.content_open||analytic.events.filter(x=>x.event_type==='content_open').reduce((v,x)=>v+x.count,0);
    $('growthConsult').textContent=totals.consult_click||analytic.events.filter(x=>x.event_type==='consult_click').reduce((v,x)=>v+x.count,0);
    $('growthIdentity').textContent=verification.items.filter(x=>x.status==='pending').length;
    const status=$('growthSystem');status.replaceChildren();
    [['데이터베이스',system.database==='connected'],['Google OAuth',system.google_oauth],['Gemini',system.gemini],['운영 게시판',system.native_bridge],['구독 웹훅',system.billing_webhook]].forEach(([label,good])=>status.append(growthText('span',label+' · '+(good?'설정 확인':'설정 필요'),good?'tag':'tag sponsor')));
    $('growthBilling').textContent=entitlements.items.filter(x=>x.active).map(x=>x.plan).join(', ')||'활성화된 유료 구독 없음';
    renderCampaigns();renderBoardOrder();renderVerifications(verification.items);
  }catch(e){gErr(e)}
}
function renderVerifications(items){const root=$('growthVerify');root.replaceChildren();if(!items.length){root.append(growthText('div','전문자격 인증 요청이 없습니다.','empty'));return}for(const v of items){let r=document.createElement('div');r.className='sort-card';r.append(growthText('span','신청자 '+v.user_id.slice(0,8)+' · 등록정보 '+v.professional_number+' · '+v.status));if(v.status==='pending'&&me.role==='admin'){
  r.append(growthBtn('대조 후 승인',()=>verificationDecision(v.user_id,true),'btn small gold'));
  r.append(growthBtn('반려',()=>verificationDecision(v.user_id,false)));
}root.append(r)}}
async function verificationDecision(uid,approved){if(!confirm('공식 변호사 등록 여부를 수동 확인했습니까?'))return;try{await request('/api/pan/verification/'+uid,{method:'PATCH',body:JSON.stringify({approved})});display('자격정보 심사 결과를 저장했습니다.');await loadGrowth()}catch(e){gErr(e)}}
function selectedCampaigns(){return growthCampaigns.filter(x=>x.product===$('growthProduct').value)}
function renderCampaigns(){const root=$('campaignCards');root.replaceChildren();const rows=selectedCampaigns();growthOrdering=rows.map(x=>x.id);
 if(!rows.length){root.append(growthText('div','등록된 캠페인이 없습니다. 공개 승인된 광고 콘텐츠를 먼저 등록하세요.','empty'));return}
 rows.forEach((r,i)=>{const li=document.createElement('div');li.className='sort-card';li.setAttribute('draggable','true');li.dataset.id=r.id;li.tabIndex=0;
  const handle=growthText('span','⠿','drag-handle');handle.title='드래그해 순서를 변경하세요';li.append(handle);
  let label=document.createElement('div');label.append(growthText('strong',r.name));label.append(growthText('small',r.title+' · '+r.status+' · '+r.product));li.append(label);
  const tools=document.createElement('div');tools.className='actions';tools.append(growthBtn('↑',()=>moveCampaign(r.id,-1)));tools.append(growthBtn('↓',()=>moveCampaign(r.id,1)));
  tools.append(growthBtn(r.status==='active'?'일시정지':'활성화',()=>campaignStatus(r.id,r.status==='active'?'paused':'active'),r.status==='active'?'btn small secondary':'btn small gold'));li.append(tools);
  li.addEventListener('dragstart',e=>{e.dataTransfer.setData('text/plain',r.id);e.dataTransfer.effectAllowed='move';li.classList.add('is-dragging')});li.addEventListener('dragend',()=>li.classList.remove('is-dragging'));
  li.addEventListener('dragover',e=>{e.preventDefault();e.dataTransfer.dropEffect='move'});li.addEventListener('drop',e=>{e.preventDefault();const from=e.dataTransfer.getData('text/plain');if(from&&from!==r.id){const a=growthOrdering.indexOf(from),b=growthOrdering.indexOf(r.id);if(a<0||b<0)return;growthOrdering.splice(b,0,growthOrdering.splice(a,1)[0]);paintCampaignOrder()}});
  root.append(li)})}
function paintCampaignOrder(){const cards=new Map([...$('campaignCards').children].map(x=>[x.dataset.id,x]));growthOrdering.forEach(id=>{const node=cards.get(id);if(node)$('campaignCards').append(node)})}
function moveCampaign(id,d){let i=growthOrdering.indexOf(id),j=i+d;if(i<0||j<0||j>=growthOrdering.length)return;[growthOrdering[i],growthOrdering[j]]=[growthOrdering[j],growthOrdering[i]];paintCampaignOrder()}
async function saveCampaignOrder(){try{await request('/api/growth/campaigns/reorder',{method:'POST',body:JSON.stringify({product:$('growthProduct').value,ids:growthOrdering})});display('노출 순서를 저장했습니다.');await loadGrowth()}catch(e){gErr(e)}}
async function campaignStatus(id,status){try{await request('/api/growth/campaigns/'+id,{method:'PATCH',body:JSON.stringify({status})});display(status==='active'?'광고 표시된 캠페인을 활성화했습니다.':'캠페인을 일시정지했습니다.');await loadGrowth()}catch(e){gErr(e)}}
function renderBoardOrder(){const product=$('orderProduct').value;const items=boards.filter(x=>x.product===product);boardOrdering=items.map(x=>x.id);const root=$('boardOrderCards');root.replaceChildren();items.forEach(x=>{const li=document.createElement('div');li.className='sort-card';li.dataset.id=x.id;li.draggable=true;
  li.append(growthText('span','⠿','drag-handle'));li.append(growthText('strong',x.name));li.append(growthBtn('위로',()=>moveBoard(x.id,-1)));li.append(growthBtn('아래로',()=>moveBoard(x.id,1)));
  li.addEventListener('dragstart',e=>e.dataTransfer.setData('text/plain',x.id));li.addEventListener('dragover',e=>e.preventDefault());li.addEventListener('drop',e=>{e.preventDefault();const from=e.dataTransfer.getData('text/plain');const a=boardOrdering.indexOf(from),b=boardOrdering.indexOf(x.id);if(a<0||b<0||a===b)return;boardOrdering.splice(b,0,boardOrdering.splice(a,1)[0]);paintBoardOrder()});root.append(li)})}
function paintBoardOrder(){const cards=new Map([...$('boardOrderCards').children].map(x=>[x.dataset.id,x]));boardOrdering.forEach(id=>{const node=cards.get(id);if(node)$('boardOrderCards').append(node)})}
function moveBoard(id,d){const i=boardOrdering.indexOf(id),j=i+d;if(i<0||j<0||j>=boardOrdering.length)return;[boardOrdering[i],boardOrdering[j]]=[boardOrdering[j],boardOrdering[i]];paintBoardOrder()}
async function saveBoardOrder(){try{await request('/api/boards/reorder',{method:'POST',body:JSON.stringify({product:$('orderProduct').value,ids:boardOrdering})});display('게시판 순서를 저장했습니다.');await loadAll();renderBoardOrder()}catch(e){gErr(e)}}
async function createCampaign(){const f=$('campaignForm').elements;const data={name:f.namedItem('name').value,post_id:f.namedItem('post_id').value,product:$('growthProduct').value,status:'draft'};try{await request('/api/growth/campaigns',{method:'POST',body:JSON.stringify(data)});$('campaignForm').reset();display('캠페인 초안을 등록했습니다. 광고 표시와 승인 상태를 확인한 뒤 활성화할 수 있습니다.');await loadGrowth()}catch(e){gErr(e)}}
function fillCampaignPosts(){let field=$('campaignPost');const product=$('growthProduct').value;field.replaceChildren();posts.filter(p=>p.product===product&&p.status==='published').forEach(p=>{let option=growthText('option',p.title+(p.is_sponsored?' · 광고':' · 광고 표시 없음'));option.value=p.id;field.append(option)})}
$('growthProduct').addEventListener('change',()=>{fillCampaignPosts();renderCampaigns()});$('orderProduct').addEventListener('change',renderBoardOrder);
$('saveOrderBtn').addEventListener('click',saveCampaignOrder);$('saveBoardOrderBtn').addEventListener('click',saveBoardOrder);
$('campaignForm').addEventListener('submit',e=>{e.preventDefault();createCampaign()});
$('newPostBtn').addEventListener('click',()=>{setTimeout(fillCampaignPosts,0)});
// Media dropzone uses the exact same native upload form and server validations as file picker.
const drop=$('uploadBlock');if(drop){drop.setAttribute('aria-label','첨부파일을 선택하거나 여기로 끌어놓으세요.');drop.classList.add('drop-target');['dragover','dragenter'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('drag-active')}));['dragleave','dragend','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('drag-active')}));drop.addEventListener('drop',e=>{if(!e.dataTransfer.files?.length)return;const dt=new DataTransfer();dt.items.add(e.dataTransfer.files[0]);$('uploadFile').files=dt.files;display('파일을 선택했습니다. 첨부 저장 버튼을 눌러 업로드하세요.')})}
