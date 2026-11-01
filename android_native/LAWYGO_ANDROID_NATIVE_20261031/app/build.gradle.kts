plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "site.lexid.lawygo"
    compileSdk = 36
    defaultConfig {
        applicationId = "site.lexid.lawygo"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0-beta"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    flavorDimensions += "product"
    productFlavors {
        create("suite") {
            dimension = "product"
            resValue("string", "app_name", "LAWYGO 통합")
            buildConfigField("String", "START_PRODUCT", "\"HOME\"")
        }
        create("journal") {
            dimension = "product"
            applicationIdSuffix = ".journal"
            resValue("string", "app_name", "LAWYGO 저널")
            buildConfigField("String", "START_PRODUCT", "\"JOURNAL\"")
        }
        create("channel") {
            dimension = "product"
            applicationIdSuffix = ".channel"
            resValue("string", "app_name", "LAWYGO 채널")
            buildConfigField("String", "START_PRODUCT", "\"CHANNEL\"")
        }
        create("pan") {
            dimension = "product"
            applicationIdSuffix = ".pan"
            resValue("string", "app_name", "LAWYGO 판")
            buildConfigField("String", "START_PRODUCT", "\"PAN\"")
        }
        create("wiki") {
            dimension = "product"
            applicationIdSuffix = ".wiki"
            resValue("string", "app_name", "LAWYGO 위키")
            buildConfigField("String", "START_PRODUCT", "\"WIKI\"")
        }
        create("note") {
            dimension = "product"
            applicationIdSuffix = ".note"
            resValue("string", "app_name", "LAWYGO 노트")
            buildConfigField("String", "START_PRODUCT", "\"NOTE\"")
        }
        create("pro") {
            dimension = "product"
            applicationIdSuffix = ".pro"
            resValue("string", "app_name", "LAWYGO 프로")
            buildConfigField("String", "START_PRODUCT", "\"PRO\"")
        }
    }
    // Optional upload-key signing: do not commit the keystore or passwords.
    val signingFile = System.getenv("LAWYGO_UPLOAD_KEYSTORE")
    if (!signingFile.isNullOrBlank()) {
        signingConfigs.create("upload") {
            storeFile = file(signingFile)
            storePassword = System.getenv("LAWYGO_UPLOAD_STORE_PASSWORD")
            keyAlias = System.getenv("LAWYGO_UPLOAD_KEY_ALIAS")
            keyPassword = System.getenv("LAWYGO_UPLOAD_KEY_PASSWORD")
        }
    }
    buildTypes {
        getByName("release") {
            isMinifyEnabled = false
            isDebuggable = false
            if (signingConfigs.findByName("upload") != null) signingConfig = signingConfigs.getByName("upload")
        }
        getByName("debug") { applicationIdSuffix = ".debug" }
    }
    buildFeatures { compose = true; buildConfig = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    packaging { resources { excludes += "/META-INF/{AL2.0,LGPL2.1}" } }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2025.10.00")
    implementation(composeBom)
    androidTestImplementation(composeBom)
    implementation("androidx.activity:activity-compose:1.11.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.10.0")
    implementation("androidx.work:work-runtime-ktx:2.10.4")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("androidx.credentials:credentials:1.5.0")
    implementation("androidx.credentials:credentials-play-services-auth:1.5.0")
    implementation("com.google.android.libraries.identity.googleid:googleid:1.2.1")
    debugImplementation("androidx.compose.ui:ui-tooling")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
