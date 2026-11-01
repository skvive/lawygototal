package site.lexid.lawygo

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import java.io.ByteArrayOutputStream
import org.json.JSONObject
import java.io.IOException
import java.net.CookieHandler
import java.net.CookieManager
import java.net.CookiePolicy
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.util.concurrent.atomic.AtomicReference

/** Session cookies remain in process memory: restart requires authentication. */
class ApiClient(private val context: Context) {
    private val cookies = CookieManager(null, CookiePolicy.ACCEPT_ORIGINAL_SERVER)
    private val current = AtomicReference("")
    fun baseUrl(): String = current.get()
    fun googleClientId(): String = context.getSharedPreferences("lawygo_config",Context.MODE_PRIVATE).getString("google_client_id","") ?: ""
    fun setGoogleClientId(clientId:String) {
        require(clientId.isBlank() || clientId.trim().endsWith(".apps.googleusercontent.com")) { "Google 웹 클라이언트 ID를 확인하세요." }
        context.getSharedPreferences("lawygo_config",Context.MODE_PRIVATE).edit().putString("google_client_id",clientId.trim()).apply()
    }

    fun configure(url: String) {
        val clean = url.trim().trimEnd('/')
        require(clean.startsWith("https://") && URI(clean).host != null && URI(clean).userInfo == null && URI(clean).port in listOf(-1,443)) {
            "운영 서버는 HTTPS 주소와 기본 443 포트를 사용해야 합니다."
        }
        require(!clean.contains('?') && !clean.contains('#')) { "API 주소 형식이 올바르지 않습니다." }
        cookies.cookieStore.removeAll()
        current.set(clean)
        context.getSharedPreferences("lawygo_config", Context.MODE_PRIVATE).edit().putString("api_base", clean).apply()
    }

    fun restoreConfig() {
        val v = context.getSharedPreferences("lawygo_config", Context.MODE_PRIVATE).getString("api_base", "") ?: ""
        if (v.isNotBlank()) runCatching { configure(v) }
    }

    @Synchronized fun request(path: String, method: String = "GET", body: JSONObject? = null): JSONObject {
        val base = current.get()
        if (base.isBlank()) throw IOException("설정에서 LAWYGO API 서버의 HTTPS 주소를 입력하세요.")
        require(path.startsWith("/") && !path.startsWith("//")) { "절대경로만 허용합니다." }
        val uri = URI(base + path)
        require(uri.host == URI(base).host && uri.scheme == "https") { "허용되지 않은 서버 주소입니다." }
        val connection = URL(uri.toString()).openConnection() as HttpURLConnection
        connection.instanceFollowRedirects = false
        connection.connectTimeout = 12000
        connection.readTimeout = 20000
        connection.requestMethod = method
        connection.setRequestProperty("Accept", "application/json")
        val cookieMap = cookies.get(uri, emptyMap())
        cookieMap["Cookie"]?.let { connection.setRequestProperty("Cookie", it.joinToString("; ")) }
        if(method != "GET") {
            val csrf = cookies.cookieStore.cookies.firstOrNull { it.name == "lawygo_cms_csrf" }?.value
            if(csrf != null) connection.setRequestProperty("X-CSRF-Token", csrf)
            if(body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.outputStream.use { it.write(body.toString().toByteArray(StandardCharsets.UTF_8)) }
            }
        }
        try {
            val setCookies = connection.headerFields.filterKeys { it?.equals("Set-Cookie", true) == true }
            cookies.put(uri, setCookies)
            if(connection.responseCode in 300..399) throw IOException("예상하지 못한 리디렉션이 발생했습니다.")
            val stream = if(connection.responseCode < 400) connection.inputStream else connection.errorStream
            val txt = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() } ?: "{}"
            val result = JSONObject(txt)
            if(connection.responseCode >= 400) throw ApiFailure(connection.responseCode, result.optString("detail",result.optString("error", "요청 실패")))
            return result
        } finally { connection.disconnect() }
    }
    /** SAF picker only; no broad media/storage permissions. 6MB hard limit before upload. */
    @Synchronized fun upload(postId: String, contentUri: Uri): JSONObject {
        require(postId.matches(Regex("[a-f0-9]{32}"))) { "게시글 ID가 올바르지 않습니다." }
        val mime = context.contentResolver.getType(contentUri) ?: ""
        require(mime in setOf("application/pdf","image/png","image/jpeg","image/webp")) { "PDF·PNG·JPEG·WebP만 첨부할 수 있습니다." }
        val maxBytes = 6*1024*1024
        val bytes = ByteArrayOutputStream()
        context.contentResolver.openInputStream(contentUri)?.use { input ->
            val b = ByteArray(8192)
            while(true) { val n=input.read(b);if(n<0) break;bytes.write(b,0,n);require(bytes.size()<=maxBytes) { "6MB 이하 파일을 선택하세요." } }
        } ?: throw IOException("첨부 파일을 열 수 없습니다.")
        val name = "attachment." + when(mime) {"application/pdf"->"pdf";"image/png"->"png";"image/webp"->"webp";else->"jpg"}
        val boundary="LAWYGO"+java.util.UUID.randomUUID().toString().replace("-","")
        val base=current.get();if(base.isBlank()) throw IOException("서버 연결이 필요합니다.")
        val uri=URI("$base/api/media?post_id=$postId")
        val con=URL(uri.toString()).openConnection() as HttpURLConnection
        con.instanceFollowRedirects=false;con.connectTimeout=12000;con.readTimeout=30000;con.requestMethod="POST";con.doOutput=true
        cookies.get(uri, emptyMap())["Cookie"]?.let{con.setRequestProperty("Cookie",it.joinToString("; "))}
        cookies.cookieStore.cookies.firstOrNull{it.name=="lawygo_cms_csrf"}?.value?.let{con.setRequestProperty("X-CSRF-Token",it)}
        con.setRequestProperty("Content-Type","multipart/form-data; boundary=$boundary")
        try {
            con.outputStream.use {o ->
                o.write("--$boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"$name\"\r\nContent-Type: $mime\r\n\r\n".toByteArray())
                o.write(bytes.toByteArray());o.write("\r\n--$boundary--\r\n".toByteArray())
            }
            val raw=(if(con.responseCode>=400)con.errorStream else con.inputStream)?.bufferedReader()?.use{it.readText()} ?: "{}"
            val result=JSONObject(raw)
            if(con.responseCode>=400) throw ApiFailure(con.responseCode,result.optString("detail","업로드 실패"))
            return result
        }finally{con.disconnect()}
    }
    fun logoutLocal() { cookies.cookieStore.removeAll() }

    companion object { fun query(q: String) = URLEncoder.encode(q, "UTF-8") }
}
class ApiFailure(val code: Int, override val message: String): IOException("$code: $message")
