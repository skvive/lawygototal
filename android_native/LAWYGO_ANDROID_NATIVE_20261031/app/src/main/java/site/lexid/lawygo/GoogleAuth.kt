package site.lexid.lawygo

import android.content.Context
import androidx.credentials.CredentialManager
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject

/** Google returns a signed ID token; only server verification establishes a LAWYGO session. */
object GoogleAuth {
    suspend fun authenticate(context: Context,api:ApiClient,clientId:String,link:Boolean):JSONObject {
        require(clientId.endsWith(".apps.googleusercontent.com")) { "Google 웹 클라이언트 ID를 등록하세요." }
        val challenge=withContext(Dispatchers.IO){api.request("/api/mobile/google/challenge")}
        val nonce=challenge.getString("nonce")
        val option=GetSignInWithGoogleOption.Builder(clientId).setNonce(nonce).build()
        val request=GetCredentialRequest.Builder().addCredentialOption(option).build()
        val returned=CredentialManager.create(context).getCredential(context,request)
        val custom=returned.credential as? CustomCredential ?: error("Google 자격증명을 받지 못했습니다.")
        require(custom.type==GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL) { "지원하지 않는 Google 인증입니다." }
        val token=GoogleIdTokenCredential.createFrom(custom.data).idToken
        val payload=JSONObject().put("id_token",token).put("nonce",nonce)
        return withContext(Dispatchers.IO){api.request(if(link)"/api/mobile/google/link" else "/api/mobile/google/login","POST",payload)}
    }
}
