[app]
title = UTC-IA
package.name = utc_ia
package.domain = org.utcia
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,json
version = 1.1
requirements = python3,kivy,google-genai
orientation = portrait
fullscreen = 0

# Gemini necesita acceso a Internet.
android.permissions = android.permission.INTERNET

# Android/Python-for-Android settings.
android.api = 35
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True

# Generate a debug APK with `buildozer android debug`.
android.debug_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
