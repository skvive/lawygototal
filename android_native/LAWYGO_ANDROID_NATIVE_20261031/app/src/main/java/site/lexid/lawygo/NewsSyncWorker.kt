package site.lexid.lawygo

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.WorkManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

/** Device refreshes public news cache; server independently schedules RSS ingestion. */
class NewsSyncWorker(ctx: Context, params: WorkerParameters): CoroutineWorker(ctx,params) {
    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val api = ApiClient(applicationContext); api.restoreConfig()
        if(api.baseUrl().isBlank()) return@withContext Result.success()
        try { LocalCache(applicationContext).store(ApiPaths.JOURNAL, api.request(ApiPaths.JOURNAL));Result.success() }
        catch(e: Exception) { Result.retry() }
    }
    companion object {
        fun enable(context: Context) {
            val req = PeriodicWorkRequestBuilder<NewsSyncWorker>(6,TimeUnit.HOURS).build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork("public-news-cache",ExistingPeriodicWorkPolicy.KEEP,req)
        }
    }
}
