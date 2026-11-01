package site.lexid.lawygo

import android.content.Context
import org.json.JSONObject
import java.security.MessageDigest

/** Cache contains public GET response only. Private NOTE/PRO/HUB cannot be cached. */
class LocalCache(private val context: Context) {
    private val preferences = context.getSharedPreferences("lawygo_public_cache", Context.MODE_PRIVATE)
    fun store(path: String, payload: JSONObject) {
        if (!isPublic(path)) return
        // Authenticated authors can see their pending items in /api/posts; never store those offline.
        val safe = if (path.startsWith("/api/posts?product=channel")) {
            val filtered=org.json.JSONArray()
            val items=payload.optJSONArray("items")
            if(items!=null) for(i in 0 until items.length()) {
                val r=items.optJSONObject(i) ?: continue
                if(r.optString("status")=="published" && r.optString("visibility")=="public") filtered.put(r)
            }
            JSONObject().put("items",filtered).put("total",filtered.length())
        } else payload
        preferences.edit().putString(key(path),safe.toString()).apply()
    }
    fun load(path: String): JSONObject? = if(isPublic(path)) preferences.getString(key(path),null)?.let { runCatching { JSONObject(it) }.getOrNull() } else null
    fun clear() = preferences.edit().clear().apply()
    private fun isPublic(path: String): Boolean = path.startsWith("/api/journal/news") || path.startsWith("/api/posts?product=channel") || path.startsWith("/api/growth/feed") || path.startsWith("/api/wiki/search")
    private fun key(path: String): String = MessageDigest.getInstance("SHA-256").digest(path.toByteArray()).joinToString("") { "%02x".format(it) }
}
