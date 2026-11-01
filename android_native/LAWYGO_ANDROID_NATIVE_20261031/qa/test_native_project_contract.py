from pathlib import Path
import re, unittest, xml.etree.ElementTree as ET
BASE=Path(__file__).resolve().parents[1]
UI=(BASE/'app/src/main/java/site/lexid/lawygo/MainActivity.kt').read_text()
API=(BASE/'app/src/main/java/site/lexid/lawygo/ApiClient.kt').read_text()
GRADLE=(BASE/'app/build.gradle.kts').read_text()
BACK=(BASE/'backend_server/app.py').read_text()

class NativeProjectContract(unittest.TestCase):
 def test_targets_android_16(self): self.assertIn('targetSdk = 36',GRADLE)
 def test_compile_sdk_36(self): self.assertIn('compileSdk = 36',GRADLE)
 def test_native_not_webview(self):self.assertNotIn('WebView(',UI);self.assertIn('setContent { LawygoApp(client) }',UI)
 def test_seven_installable_variants(self):
  for name in ['suite','journal','channel','pan','wiki','note','pro']:self.assertIn(f'create("{name}")',GRADLE)
 def test_no_http_cleartext_release(self):self.assertIn('android:usesCleartextTraffic="false"',(BASE/'app/src/main/AndroidManifest.xml').read_text())
 def test_manifest_valid(self):ET.parse(BASE/'app/src/main/AndroidManifest.xml')
 def test_no_ignored_pan_category_buttons(self):self.assertIn('FilterChip(',UI);self.assertNotIn('AssistChip(onClick={}',UI)
 def test_feed_click_executed(self):self.assertIn('if(product==Product.JOURNAL) onOpen(',UI)
 def test_csrf_cookie(self):self.assertIn('lawygo_cms_csrf',API);self.assertIn('X-CSRF-Token',API)
 def test_ssl_only(self):self.assertIn('clean.startsWith("https://")',API)
 def test_note_private_creation(self):self.assertIn('if(page==Product.NOTE)"private"',UI)
 def test_explicit_ai_consent(self):self.assertIn('동의하고 분석',UI);self.assertIn('put("consent",true)',UI)
 def test_backend_has_all_pages(self):
  for path in ['/api/journal/news','/api/wiki/search','/api/posts','/api/mobile/google/challenge','/api/mobile/google/link','/api/mobile/google/login']:
   if '/api/mobile' in path:self.assertIn(path,(BASE/'backend_server/mobile_auth.py').read_text())
   elif '/api/journal/news' in path:self.assertIn(path,(BASE/'backend_server/editorial_v5.py').read_text())
   else:self.assertIn(path,BACK)
 def test_pro_legacy_qualified(self):self.assertIn('기존 운영 서비스',UI)
 def test_work_manager_public_only(self):
  code=(BASE/'app/src/main/java/site/lexid/lawygo/NewsSyncWorker.kt').read_text()
  self.assertIn('ApiPaths.JOURNAL',code);self.assertNotIn('ApiPaths.NOTE',code)
 def test_public_cache_not_notes(self):self.assertNotIn('product=note',(BASE/'app/src/main/java/site/lexid/lawygo/LocalCache.kt').read_text())
 def test_no_embedded_credentials(self):
  for path in list((BASE/'app').rglob('*.kt')):
   self.assertNotRegex(path.read_text(),r'(?i)(private_key|api_key|client_secret)\s*[:=]\s*"[a-z0-9_-]{16,}"')
 def test_unsigned_release_safety(self):self.assertIn('LAWYGO_UPLOAD_KEYSTORE',GRADLE)

if __name__=='__main__':unittest.main()
