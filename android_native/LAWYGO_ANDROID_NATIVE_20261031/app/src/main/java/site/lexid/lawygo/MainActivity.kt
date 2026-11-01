package site.lexid.lawygo

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Locale

private val Navy = Color(0xFF102B43)
private val Gold = Color(0xFFB08A52)
private val Paper = Color(0xFFF8F7F3)
private val Ink = Color(0xFF263545)
private val Muted = Color(0xFF697784)

class MainActivity: ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        NewsSyncWorker.enable(applicationContext)
        val client = ApiClient(applicationContext)
        client.restoreConfig()
        setContent { LawygoApp(client) }
    }
}

@Composable
fun LawygoApp(api: ApiClient) {
    val ctx = LocalContext.current
    val cache = remember { LocalCache(ctx.applicationContext) }
    val scope = rememberCoroutineScope()
    var page by remember { mutableStateOf(Product.entries.firstOrNull{it.name==BuildConfig.START_PRODUCT} ?: Product.HOME) }
    var detail by remember { mutableStateOf<JSONObject?>(null) }
    var mode by remember { mutableStateOf("list") }
    var signedUser by remember { mutableStateOf<JSONObject?>(null) }
    var server by remember { mutableStateOf(api.baseUrl()) }
    var boardsForEditor by remember { mutableStateOf(listOf<JSONObject>()) }
    var modules by remember { mutableStateOf(listOf<JSONObject>()) }
    var message by remember { mutableStateOf("") }
    var reloading by remember { mutableIntStateOf(0) }
    var busy by remember { mutableStateOf(false) }
    var payload by remember { mutableStateOf(JSONObject()) }
    var rows by remember { mutableStateOf(listOf<JSONObject>()) }
    var offline by remember { mutableStateOf(false) }
    fun fetch(p: String, done: (JSONObject) -> Unit) {
        scope.launch {
            busy = true
            try {
                val data = withContext(Dispatchers.IO) { api.request(p) }
                cache.store(p,data); offline = false; done(data); message = ""
            } catch(e: Exception) {
                val cached = cache.load(p)
                if(cached != null) { offline = true; done(cached);message = "오프라인에 저장된 공개 데이터입니다." }
                else { rows=emptyList();message=e.message ?: "서버 연결 실패" }
            } finally { busy = false }
        }
    }
    fun reload() {reloading++}
    fun go(to: Product) {page=to;detail=null;mode="list";reload()}
    fun openDetail(item:JSONObject) {
        detail=item;mode="detail"
        val id=item.optString("id")
        if(id.isNotBlank() && page!=Product.JOURNAL) fetch("/api/posts/$id") { detail=it }
    }
    fun openModules() {
        mode="modules"
        fetch("/api/hub/modules") { modules=it.optJSONArray("items")?.objects().orEmpty() }
    }
    fun updateModule(module:JSONObject, enabled:Boolean) {
        val id=module.optString("id")
        scope.launch {
            busy=true
            try {
                withContext(Dispatchers.IO) {
                    api.request("/api/hub/modules/$id","PATCH",JSONObject().put("version",module.optInt("version",1)).put("enabled",enabled))
                }
                message="모듈 상태를 저장했습니다.";openModules()
            }catch(e:Exception){message=e.message.orEmpty()}finally{busy=false}
        }
    }
    fun openEditor() {
        if(detail!=null) {mode="edit";return}
        fetch("/api/boards?product=${page.name.lowercase()}") { boardsForEditor=it.optJSONArray("items")?.objects().orEmpty() }
        mode="edit"
    }
    BackHandler(detail != null || mode != "list") { detail = null;mode = "list" }
    LaunchedEffect(server) {
        if(server.isNotBlank()) runCatching {
            signedUser = withContext(Dispatchers.IO) { api.request(ApiPaths.ME) }
        }
    }
    LaunchedEffect(page,reloading,server,signedUser) {
        rows=emptyList();payload=JSONObject()
        if(server.isBlank() || page==Product.HOME) return@LaunchedEffect
        if(page==Product.NOTE && signedUser == null) {message="노트는 로그인 후 이용할 수 있습니다.";return@LaunchedEffect}
        if(page==Product.HUB && signedUser == null) {message="관리 기능은 로그인 후 이용할 수 있습니다.";return@LaunchedEffect}
        val path = if(page==Product.WIKI) "" else page.endpoint
        if(path.isNotBlank()) fetch(path) { j -> payload=j;rows=j.optJSONArray("items")?.objects().orEmpty() }
    }
    MaterialTheme(colorScheme=lightColorScheme(primary=Navy,secondary=Gold,background=Paper,surface=Color.White,onPrimary=Color.White)) {
        Scaffold(
            topBar = {
                Surface(color=Navy) {
                    Row(Modifier.fillMaxWidth().height(60.dp).padding(horizontal=16.dp),verticalAlignment=Alignment.CenterVertically) {
                        Text("L",color=Gold,fontSize=30.sp,fontWeight=FontWeight.Black)
                        Spacer(Modifier.width(10.dp));Column(Modifier.weight(1f)) {
                            Text("LAWYGO",color=Color.White,fontSize=16.sp,fontWeight=FontWeight.Bold,letterSpacing=2.sp)
                            Text(page.subtitle,color=Color(0xFFD1D8E0),fontSize=10.sp)
                        }
                        if(signedUser!=null) TextButton(onClick={go(Product.HUB)}) {Text("관리",color=Color.White)}
                        IconButton(onClick={mode="settings"}) {Icon(Icons.Default.Settings,"서버 설정",tint=Color.White)}
                    }
                }
            },
            bottomBar = {
                NavigationBar(containerColor=Color.White) {
                    listOf(Product.HOME,Product.JOURNAL,Product.PAN,Product.WIKI,Product.NOTE).forEach { p ->
                        val icon = when(p){Product.HOME->Icons.Default.Home;Product.JOURNAL->Icons.Default.Article;Product.PAN->Icons.Default.Groups;Product.WIKI->Icons.Default.MenuBook;else->Icons.Default.EditNote}
                        NavigationBarItem(selected=page==p,onClick={go(p)},icon={Icon(icon,p.label)},label={Text(p.label,fontSize=10.sp)})
                    }
                }
            }
        ) { padding ->
            Column(Modifier.padding(padding).fillMaxSize()) {
                if(busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                if(message.isNotBlank()) Surface(color=Color(0xFFFFF0DA),modifier=Modifier.fillMaxWidth()) {
                    Row(Modifier.padding(10.dp),verticalAlignment=Alignment.CenterVertically) {
                        Text(message,Modifier.weight(1f),fontSize=12.sp,color=Ink)
                        IconButton(onClick={message=""}){Icon(Icons.Default.Close,"닫기")}
                    }
                }
                when(mode) {
                    "modules" -> ModuleManagerScreen(modules,onBack={mode="list"},onToggle={m,b->updateModule(m,b)},onRefresh={openModules()})
                    "settings" -> SettingsScreen(server,googleId=api.googleClientId(), onSave={value,google ->
                        try {api.configure(value);api.setGoogleClientId(google);server=api.baseUrl();signedUser=null;cache.clear();mode="list";reload()}
                        catch(e:Exception) {message=e.message.orEmpty()}
                    },onClose={mode="list"})
                    "login" -> LoginScreen(onGoogle={link ->
                        scope.launch {busy=true;try {
                            val result=GoogleAuth.authenticate(ctx,api,api.googleClientId(),link)
                            if(link){message="Google 계정이 연결되었습니다.";mode="list"}
                            else {signedUser=result;message="Google 계정으로 로그인했습니다.";mode="list";reload()}
                        }catch(e:Exception){message=e.message.orEmpty()}finally{busy=false}}
                    },alreadyLoggedIn=signedUser!=null,onLogin={ email,pass,tenant ->
                        scope.launch {busy=true;try {
                            val request=JSONObject().put("email",email).put("password",pass).put("tenant",tenant)
                            signedUser=withContext(Dispatchers.IO){api.request(ApiPaths.LOGIN,"POST",request)}
                            mode="list";message="로그인했습니다.";reload()
                        }catch(e:Exception){message=e.message.orEmpty()}finally{busy=false}}
                    },onClose={mode="list"})
                    "edit" -> PostEditScreen(product=page, existing=detail,boards=boardsForEditor,
                        onCancel={mode="list"},onSave={ title,body,board,kind ->
                            scope.launch {busy=true;try {
                                val json=JSONObject().put("title",title).put("body",body)
                                val path:String;val verb:String
                                if(detail==null) {
                                    json.put("board_id",board).put("kind",kind).put("summary",body.take(150))
                                    json.put("status",if(page==Product.NOTE)"draft" else "pending").put("visibility",if(page==Product.NOTE)"private" else "public")
                                    json.put("is_sponsored",false);path=ApiPaths.POSTS;verb="POST"
                                } else {json.put("version",detail?.optInt("version",1));path=ApiPaths.POSTS+"/"+detail?.optString("id");verb="PATCH"}
                                withContext(Dispatchers.IO){api.request(path,verb,json)}
                                detail=null;mode="list";message="저장했습니다. 공개 콘텐츠는 편집 승인 후 게시됩니다.";reload()
                            }catch(e:Exception){message=e.message.orEmpty()}finally{busy=false}}
                        })
                    "detail" -> DetailScreen(detail,onBack={mode="list";detail=null},
                        onEdit={openEditor()},onExternal={url->openExternal(ctx,url)},
                        onDelete={id -> scope.launch {busy=true;try { withContext(Dispatchers.IO){api.request("/api/posts/$id","DELETE")};detail=null;mode="list";message="삭제했습니다.";reload() }catch(e:Exception){message=e.message.orEmpty()}finally{busy=false}}},
                        onApprove={id,version -> scope.launch{busy=true;try{withContext(Dispatchers.IO){api.request("/api/posts/$id","PATCH",JSONObject().put("version",version).put("status","published"))};detail=null;mode="list";message="게시를 승인했습니다.";reload()}catch(e:Exception){message=e.message.orEmpty()}finally{busy=false}}},
                        onUpload={uri -> scope.launch{busy=true;try{val id=detail?.optString("id") ?: "";withContext(Dispatchers.IO){api.upload(id,uri)};message="첨부파일을 등록했습니다."}
                            catch(e:Exception){message=e.message.orEmpty()}finally{busy=false}}},
                        onAnalyze={id,update -> scope.launch{busy=true;try{val j=withContext(Dispatchers.IO){api.request("/api/note/$id/ai-analyze","POST",JSONObject().put("consent",true))};update(j.optJSONObject("result")?.toString(2)?:j.toString())}
                            catch(e:Exception){message=e.message.orEmpty()}finally{busy=false}}},
                        canApprove=signedUser?.optString("role") in listOf("admin","editor"),
                        canEdit=signedUser!=null && (page==Product.NOTE|| signedUser?.optString("role") in listOf("admin","editor")|| detail?.optString("author_id")==signedUser?.optString("id")))
                    else -> {
                        when(page){
                            Product.HOME -> HomeScreen(onGo={go(it)},onLogin={mode="login"},onLogout={scope.launch {
                                runCatching {withContext(Dispatchers.IO){api.request(ApiPaths.LOGOUT,"POST",JSONObject())}}
                                api.logoutLocal();signedUser=null;cache.clear();message="로그아웃했습니다.";reload()
                            }},user=signedUser)
                            Product.WIKI -> WikiScreen(api,cache,onDetail={openDetail(it)},onMessage={message=it})
                            Product.HUB -> HubScreen(payload,onRefresh={reload()},onManage={go(it)},onModules={openModules()})
                            Product.PRO -> ProScreen(onGo={go(Product.HUB)},onLogin={mode="login"},onExternal={openExternal(ctx,"https://pro.lawygo.com")})
                            Product.NOTE,Product.CHANNEL,Product.PAN,Product.JOURNAL -> FeedScreen(page,rows,offline,
                                onRefresh={reload()},onSelect={openDetail(it)},onCreate={openEditor()},
                                onGo={go(it)},canWrite=signedUser!=null && page!=Product.JOURNAL,
                                onOpen={openExternal(ctx,it)})
                        }
                    }
                }
            }
        }
    }
}

private fun JSONArray.objects():List<JSONObject> = (0 until length()).mapNotNull { optJSONObject(it) }
private fun openExternal(ctx:android.content.Context,url:String) {
    try {val u=Uri.parse(url);if(u.scheme=="https") ctx.startActivity(Intent(Intent.ACTION_VIEW,u))}
    catch(_:Exception){}
}

@Composable private fun SectionHeader(kicker:String,title:String,description:String="") {
    Column(Modifier.padding(top=14.dp,bottom=15.dp)) {
        Text(kicker,color=Gold,fontSize=11.sp,letterSpacing=2.sp,fontWeight=FontWeight.Bold)
        Text(title,fontSize=29.sp,lineHeight=33.sp,color=Navy,fontWeight=FontWeight.Bold)
        if(description.isNotBlank()) Text(description,Modifier.padding(top=6.dp),fontSize=13.sp,color=Muted)
        HorizontalDivider(Modifier.padding(top=15.dp),color=Gold.copy(alpha=.6f))
    }
}
@Composable private fun HomeScreen(onGo:(Product)->Unit,onLogin:()->Unit,onLogout:()->Unit,user:JSONObject?) {
    LazyColumn(contentPadding=PaddingValues(19.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
        item {SectionHeader("LEGAL INTELLIGENCE","법률 지식의 새로운 기준","전문 정보·콘텐츠·업무 도구를 하나의 앱에서 만나보세요.")}
        item {Text("오늘의 LAWYGO",fontSize=18.sp,color=Navy,fontWeight=FontWeight.SemiBold)}
        items(listOf(Product.JOURNAL,Product.CHANNEL,Product.PAN,Product.WIKI,Product.NOTE,Product.PRO,Product.HUB)) {p ->
            Card(onClick={onGo(p)},colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(14.dp),modifier=Modifier.fillMaxWidth()) {
                Row(Modifier.fillMaxWidth().padding(18.dp),verticalAlignment=Alignment.CenterVertically){
                    Column(Modifier.weight(1f)) {Text("LAWYGO ${p.name}",fontSize=10.sp,letterSpacing=1.4.sp,color=Gold,fontWeight=FontWeight.SemiBold)
                        Text(p.label,fontSize=20.sp,fontWeight=FontWeight.Bold,color=Navy);Text(p.subtitle,fontSize=12.sp,color=Muted)}
                    Icon(Icons.Default.ChevronRight,null,tint=Navy)
                }
            }
        }
        item {if(user==null) Button(onClick=onLogin,Modifier.fillMaxWidth()){Text("회원 로그인")} else { OutlinedButton(onClick=onLogin,Modifier.fillMaxWidth()){Text("Google 계정 연결 설정")};OutlinedButton(onClick=onLogout,Modifier.fillMaxWidth()){Text("${user.optString("name",user.optString("display_name"))} · 로그아웃")} }}
        item {Text("법률 정보는 일반 참고자료이며 개별 사건에 대한 법률 자문을 대체하지 않습니다.",fontSize=11.sp,color=Muted)}
    }
}

@Composable private fun FeedScreen(product:Product,rows:List<JSONObject>,offline:Boolean,onRefresh:()->Unit,
    onSelect:(JSONObject)->Unit,onCreate:()->Unit,onGo:(Product)->Unit,canWrite:Boolean,onOpen:(String)->Unit) {
    val kicker=when(product){Product.JOURNAL->"THE DAILY BRIEF";Product.PAN->"EXPERT CONTENT";Product.CHANNEL->"LEGAL VOICES";Product.NOTE->"PRIVATE WORKSPACE";else->"LAWYGO"}
    var categoryFilter by remember {mutableStateOf("")}
    val visibleRows=if(categoryFilter.isBlank()) rows else rows.filter { it.optString("title").contains(categoryFilter)||it.optString("summary").contains(categoryFilter) }
    LazyColumn(contentPadding=PaddingValues(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
        item {SectionHeader(kicker,"로이고 ${product.label}",product.subtitle)}
        if(product==Product.PAN) item {Row(horizontalArrangement=Arrangement.spacedBy(6.dp)) {
            listOf("전체","민사","형사","기업","부동산").forEach{cat -> FilterChip(selected=(if(cat=="전체") categoryFilter.isBlank() else categoryFilter==cat),onClick={categoryFilter=if(cat=="전체")"" else cat},label={Text(cat)})}
        }}
        item {Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp)){
            OutlinedButton(onClick=onRefresh){Icon(Icons.Default.Refresh,null);Spacer(Modifier.width(4.dp));Text("새로고침")}
            if(canWrite) Button(onClick=onCreate){Icon(Icons.Default.Add,null);Text("새 글")}
        }}
        if(offline) item {Text("오프라인에서 저장된 공개 기사만 표시합니다.",color=Gold,fontSize=12.sp)}
        if(visibleRows.isEmpty()) item {EmptyState(if(product==Product.NOTE)"로그인 후 비공개 노트를 작성하세요." else "표시할 콘텐츠가 없습니다. 서버 연결·편집 승인 상태를 확인하세요.")}
        items(visibleRows) {r ->
            val title=r.optString("title","제목 없음")
            val summary=r.optString("summary", "")
            val sponsored=r.optBoolean("is_sponsored",false)||r.optString("placement")=="광고"
            Card(onClick={if(product==Product.JOURNAL) onOpen(r.optString("url")) else onSelect(r)},
                modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(10.dp),colors=CardDefaults.cardColors(containerColor=Color.White)) {
                Column(Modifier.padding(17.dp)) {
                    Text(if(sponsored)"광고 · LAWYGO" else r.optString("source",r.optString("kind",product.label)),fontSize=11.sp,color=Gold)
                    Text(title,Modifier.padding(top=5.dp),fontSize=17.sp,fontWeight=FontWeight.Bold,color=Navy,maxLines=3,overflow=TextOverflow.Ellipsis)
                    if(summary.isNotBlank()) Text(summary,Modifier.padding(top=8.dp),fontSize=12.sp,color=Muted,maxLines=3,overflow=TextOverflow.Ellipsis)
                    Text(r.optString("published_at",r.optString("updated_at","출처 확인" )).take(16),Modifier.padding(top=10.dp),fontSize=11.sp,color=Muted)
                }
            }
        }
    }
}

@Composable private fun WikiScreen(api:ApiClient,cache:LocalCache,onDetail:(JSONObject)->Unit,onMessage:(String)->Unit) {
    val scope=rememberCoroutineScope();var query by remember {mutableStateOf("")};var results by remember{mutableStateOf(emptyList<JSONObject>())};var searching by remember{mutableStateOf(false)}
    LazyColumn(contentPadding=PaddingValues(18.dp),verticalArrangement=Arrangement.spacedBy(13.dp)) {
        item {SectionHeader("LEGAL ENCYCLOPEDIA","법률백과 검색","검수·공개된 자료만 검색하며 원문 판례와 시행 법령을 확인하세요.")}
        item {OutlinedTextField(query,{query=it},Modifier.fillMaxWidth(),label={Text("검색어 · 법률 분야 또는 판례")},singleLine=true,leadingIcon={Icon(Icons.Default.Search,null)})}
        item {Button(enabled=query.trim().length>=2&&!searching,onClick={
            scope.launch {searching=true;try{val path=ApiPaths.WIKI+"?q="+ApiClient.query(query)
                val j=withContext(Dispatchers.IO){api.request(path)};cache.store(path,j);results=j.optJSONArray("items")?.objects().orEmpty()}
                catch(e:Exception){onMessage(e.message.orEmpty());results=emptyList()}finally{searching=false}}
        },modifier=Modifier.fillMaxWidth()) {Text(if(searching)"검색 중" else "법률정보 검색")}}
        if(results.isEmpty()) item {EmptyState("공개 검수된 위키 항목을 검색하세요.")}
        items(results){r -> Card(onClick={onDetail(r)},colors=CardDefaults.cardColors(containerColor=Color.White)){
            Column(Modifier.fillMaxWidth().padding(18.dp)) {Text(r.optString("title"),fontWeight=FontWeight.Bold,color=Navy,fontSize=16.sp)
                Text(r.optString("summary"),fontSize=12.sp,color=Muted,maxLines=3)}
        }}
    }
}
@Composable private fun HubScreen(data:JSONObject,onRefresh:()->Unit,onManage:(Product)->Unit,onModules:()->Unit) {
    LazyColumn(contentPadding=PaddingValues(18.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
        item{SectionHeader("OPERATIONS HUB","통합 관리자","내 권한으로 확인할 수 있는 로이고 모듈·통계입니다.")}
        item {OutlinedButton(onClick=onRefresh){Text("통계 새로고침")};Button(onClick=onModules){Text("모듈 관리")}}
        items(listOf("posts" to "전체 게시글","boards" to "게시판","campaigns_active" to "운영 광고","lawyers_pending" to "인증 검토","newsletter_active" to "뉴스레터 구독")) {x ->
            Surface(Modifier.fillMaxWidth(),shape=RoundedCornerShape(12.dp),color=Color.White) {
                Row(Modifier.padding(17.dp),horizontalArrangement=Arrangement.SpaceBetween) {
                    Text(x.second,color=Muted)
                    val metric = if(x.first in listOf("posts","boards")) {
                        val a=data.optJSONArray(x.first);(0 until (a?.length() ?: 0)).sumOf{a?.optJSONObject(it)?.optInt("count",0) ?: 0}.toString()
                    } else data.optString(x.first,"—")
                    Text(metric,fontWeight=FontWeight.Bold,color=Navy)
                }
            }
        }
        items(listOf(Product.JOURNAL,Product.CHANNEL,Product.PAN,Product.WIKI,Product.NOTE)){p ->
            OutlinedButton(onClick={onManage(p)},Modifier.fillMaxWidth()){Text(p.label+" 콘텐츠 관리")}
        }
    }
}
@Composable private fun ModuleManagerScreen(modules:List<JSONObject>,onBack:()->Unit,onToggle:(JSONObject,Boolean)->Unit,onRefresh:()->Unit){
    LazyColumn(contentPadding=PaddingValues(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
        item{SectionHeader("MODULE OPERATIONS","모듈 관리","운영 관리자만 모듈 활성 상태를 변경할 수 있습니다.")}
        item{Row {TextButton(onClick=onBack){Text("허브로")};OutlinedButton(onClick=onRefresh){Text("새로고침")}}}
        items(modules){m-> Card(colors=CardDefaults.cardColors(containerColor=Color.White)){
            Row(Modifier.padding(16.dp).fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
                Column(Modifier.weight(1f)){
                    Text(m.optString("name"),color=Navy,fontWeight=FontWeight.Bold)
                    Text(m.optString("product").uppercase()+" · "+m.optString("module_type"),color=Muted,fontSize=11.sp)
                    Text(m.optString("description"),color=Muted,fontSize=12.sp,maxLines=2)
                }
                Switch(checked=m.optBoolean("enabled"),onCheckedChange={onToggle(m,it)})
            }
        }}
        if(modules.isEmpty()) item{EmptyState("관리 모듈 목록을 가져올 수 없습니다.")}
    }
}
@Composable private fun ProScreen(onGo:()->Unit,onLogin:()->Unit,onExternal:()->Unit) {
    Column(Modifier.verticalScroll(rememberScrollState()).padding(18.dp)) {
        SectionHeader("LEGAL PRACTICE","로이고 프로","사건·일정·서면·승인 업무를 위한 송무관리 엔진")
        Text("PRO의 완전한 업무 데이터는 기존 운영 서비스에 보관됩니다. 모바일 원본 API 연동 및 권한 검증 전에는 별도 서버 기능을 복제하지 않습니다.",color=Muted)
        Spacer(Modifier.height(18.dp));Button(onClick=onLogin,Modifier.fillMaxWidth()){Text("기존 계정 로그인")}
        OutlinedButton(onClick=onExternal,Modifier.fillMaxWidth()){Text("기존 PRO 송무관리 서비스 열기")}
        OutlinedButton(onClick=onGo,Modifier.fillMaxWidth()){Text("모듈 관리 허브")}
    }
}
@Composable private fun DetailScreen(detail:JSONObject?,onBack:()->Unit,onEdit:()->Unit,onExternal:(String)->Unit,onDelete:(String)->Unit,onApprove:(String,Int)->Unit,onUpload:(Uri)->Unit,onAnalyze:(String,(String)->Unit)->Unit,canApprove:Boolean,canEdit:Boolean) {
    if(detail==null)return
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(19.dp)) {
        TextButton(onClick=onBack){Icon(Icons.AutoMirrored.Filled.ArrowBack,null);Text("목록으로")}
        SectionHeader(detail.optString("kind","LAWYGO"),detail.optString("title","상세보기"))
        if(detail.optBoolean("is_sponsored")) Text("광고",color=Gold,fontWeight=FontWeight.Bold)
        Text(detail.optString("summary",""),fontSize=15.sp,color=Muted)
        Spacer(Modifier.height(16.dp))
        Text(detail.optString("body","내용을 불러오지 못했습니다."),fontSize=15.sp,lineHeight=24.sp,color=Ink)
        val url=detail.optString("external_url")
        if(url.startsWith("https://"))OutlinedButton(onClick={onExternal(url)}){Text("원문 열기")}
        if(canEdit) {
            Button(onClick=onEdit){Text("수정")}
            val status=detail.optString("status")
            if(canApprove && status!="published" && detail.optString("product")!="note") OutlinedButton(onClick={onApprove(detail.optString("id"),detail.optInt("version",1))}){Text("게시 승인")}
            var confirmDelete by remember { mutableStateOf(false) }
            OutlinedButton(onClick={confirmDelete=true}) {Text("삭제")}
            if(confirmDelete) AlertDialog(onDismissRequest={confirmDelete=false},title={Text("게시글 삭제")},text={Text("이 글을 휴지통으로 이동할까요?")},
                confirmButton={TextButton(onClick={confirmDelete=false;onDelete(detail.optString("id"))}){Text("삭제")}},
                dismissButton={TextButton(onClick={confirmDelete=false}){Text("취소")}})
        }
        if(detail.optString("product")=="note" && canEdit){
            val picker=rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()){uri -> if(uri!=null) onUpload(uri)}
            OutlinedButton(onClick={picker.launch(arrayOf("application/pdf","image/png","image/jpeg","image/webp"))}){Text("PDF·이미지 첨부")}
            var confirmAI by remember{mutableStateOf(false)}
            var analysis by remember{mutableStateOf("")}
            Button(onClick={confirmAI=true}){Text("AI 출처기반 분석")}
            if(confirmAI) AlertDialog(onDismissRequest={confirmAI=false},title={Text("외부 AI 전송 동의")},
                text={Text("이 노트 본문과 첨부 PDF 추출 내용이 설정된 외부 AI 제공자에게 전송됩니다. 사건·의뢰인 개인정보가 없는지 먼저 확인하세요.")},
                confirmButton={TextButton(onClick={confirmAI=false;onAnalyze(detail.optString("id")){analysis=it}}){Text("동의하고 분석")}},
                dismissButton={TextButton(onClick={confirmAI=false}){Text("취소")}})
            if(analysis.isNotBlank()) Text(analysis,color=Ink,fontSize=12.sp)
        }
        Text("개별 법률 사안은 관련 법령의 최신 시행일과 전문가의 검토를 확인하세요.",fontSize=11.sp,color=Muted)
    }
}
@Composable private fun PostEditScreen(product:Product,existing:JSONObject?,boards:List<JSONObject>,onCancel:()->Unit,onSave:(String,String,String,String)->Unit) {
    var title by remember(existing){mutableStateOf(existing?.optString("title").orEmpty())}
    var body by remember(existing){mutableStateOf(existing?.optString("body").orEmpty())}
    var board by remember(boards){mutableStateOf(boards.firstOrNull()?.optString("id") ?: "")}
    var kind by remember{mutableStateOf(when(product){Product.NOTE->"note";Product.PAN->"article";else->"article"})}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
        SectionHeader("EDITOR","${product.label} ${if(existing==null)"작성" else "수정"}","공개 콘텐츠는 승인 전까지 비공개 대기 상태입니다.")
        OutlinedTextField(title,{title=it},Modifier.fillMaxWidth(),label={Text("제목")})
        if(existing==null){
            var expanded by remember { mutableStateOf(false) }
            Box {
                OutlinedButton(onClick={expanded=true},Modifier.fillMaxWidth()){
                    Text(boards.firstOrNull { it.optString("id")==board }?.optString("name") ?: "게시판 선택")
                    Icon(Icons.Default.ArrowDropDown,null)
                }
                DropdownMenu(expanded=expanded,onDismissRequest={expanded=false}) {
                    boards.forEach { b -> DropdownMenuItem(text={Text(b.optString("name"))},onClick={board=b.optString("id");expanded=false}) }
                }
            }
            if(boards.isEmpty()) Text("관리자에서 게시판 생성 및 권한 설정이 필요합니다.",color=Gold,fontSize=12.sp)
            OutlinedTextField(kind,{kind=it},Modifier.fillMaxWidth(),label={Text("콘텐츠 유형")})}
        OutlinedTextField(body,{body=it},Modifier.fillMaxWidth().heightIn(min=180.dp),label={Text("내용")},minLines=7)
        Button(enabled=title.isNotBlank()&&body.isNotBlank()&&(existing!=null||board.isNotBlank()),onClick={onSave(title,body,board,kind)},modifier=Modifier.fillMaxWidth()){Text("저장하기")}
        OutlinedButton(onClick=onCancel,modifier=Modifier.fillMaxWidth()){Text("취소")}
    }
}
@Composable private fun LoginScreen(onGoogle:(Boolean)->Unit,alreadyLoggedIn:Boolean,onLogin:(String,String,String)->Unit,onClose:()->Unit){
    var email by remember{mutableStateOf("")};var password by remember{mutableStateOf("")};var tenant by remember{mutableStateOf("demo")}
    Column(Modifier.verticalScroll(rememberScrollState()).padding(22.dp),verticalArrangement=Arrangement.spacedBy(13.dp)) {
        SectionHeader("ACCOUNT","회원 로그인","로이고 서버 계정으로 로그인합니다.")
        OutlinedTextField(email,{email=it},Modifier.fillMaxWidth(),label={Text("이메일")},singleLine=true)
        OutlinedTextField(password,{password=it},Modifier.fillMaxWidth(),label={Text("비밀번호")},visualTransformation=PasswordVisualTransformation())
        OutlinedTextField(tenant,{tenant=it},Modifier.fillMaxWidth(),label={Text("관리번호·테넌트 (기본: demo)")})
        Button(onClick={onLogin(email,password,tenant)},enabled=email.isNotBlank()&&password.isNotBlank(),modifier=Modifier.fillMaxWidth()){Text("로그인")}
        OutlinedButton(onClick={onGoogle(false)},Modifier.fillMaxWidth()){Text("Google 계정으로 로그인")}
        if(alreadyLoggedIn) OutlinedButton(onClick={onGoogle(true)},Modifier.fillMaxWidth()){Text("현재 계정에 Google 계정 연결")}
        OutlinedButton(onClick=onClose,Modifier.fillMaxWidth()){Text("취소")}
        Text("Google 로그인은 별도 Android OAuth 설정과 기존 서버 인증 연동이 완료된 뒤 활성화해야 합니다.",fontSize=12.sp,color=Muted)
    }
}
@Composable private fun SettingsScreen(initial:String,googleId:String,onSave:(String,String)->Unit,onClose:()->Unit) {
    var server by remember{mutableStateOf(initial)}
    var google by remember{mutableStateOf(googleId)}
    Column(Modifier.verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(14.dp)) {
        SectionHeader("SETTINGS","서버 연결","로이고 API가 설치된 운영 서버의 HTTPS 주소를 입력합니다.")
        OutlinedTextField(server,{server=it},Modifier.fillMaxWidth(),label={Text("https://api.example.com")},singleLine=true)
        OutlinedTextField(google,{google=it},Modifier.fillMaxWidth(),label={Text("Google 웹 클라이언트 ID (선택)")})
        Button(onClick={onSave(server,google)},Modifier.fillMaxWidth()){Text("서버 연결 저장")}
        OutlinedButton(onClick=onClose,Modifier.fillMaxWidth()){Text("취소")}
        Text("보안을 위해 HTTP와 비표준 포트는 사용할 수 없습니다. 로컬 테스트 시 실제 HTTPS 리버스 프록시를 사용하세요.",color=Muted,fontSize=12.sp)
    }
}
@Composable private fun EmptyState(text:String){ Surface(color=Color.White,shape=RoundedCornerShape(12.dp),modifier=Modifier.fillMaxWidth()){
    Column(Modifier.padding(28.dp),horizontalAlignment=Alignment.CenterHorizontally){Icon(Icons.Default.Inbox,null,tint=Gold);Spacer(Modifier.height(8.dp));Text(text,color=Muted,textAlign=TextAlign.Center,fontSize=13.sp)}
}}
