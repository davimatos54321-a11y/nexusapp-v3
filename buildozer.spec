[app]

title = Nexus App
package.name = nexusapp
package.domain = org.nexus
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,openssl,requests,urllib3,certifi,idna,charset-normalizer
android.package_format = apk
fullscreen = 0
android.androidx = True
android.api = 33
android.minapi = 21
android.ndk = r25b

# Caminhos absolutos forçados para o Buildozer não tentar baixar nada sozinho
android.ndk_path = /home/runner/.buildozer/android/platform/android-ndk-r25b
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk

android.permissions = INTERNET
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
bin_dir = ./bin
