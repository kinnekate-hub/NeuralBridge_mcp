plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.neuralbridge"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.neuralbridge"
        minSdk = 27
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
}

dependencies {
    implementation("ai.nexa:core:0.0.19")
}
