[app]

title = Janus Call
package.name = januscall
package.domain = org.januscall.app

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,json
version = 0.1.0

# Mantém o build base rápido e estável; o main.py faz fallback automático se faltar lib nativa
requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CAMERA,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS,READ_CONTACTS,CALL_PHONE

android.enable_androidx = True
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True

p4a.branch = master
android.archs = arm64-v8a


[buildozer]

log_level = 1
warn_on_root = 1
