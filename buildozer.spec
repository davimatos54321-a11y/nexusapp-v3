[app]

# (str) Title of your application
title = Nexus App

# (str) Package name
package.name = nexusapp

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (str) Source where the app lives
source.dir = .

# (list) Source files to include (let it blank to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
requirements = python3,kivy,openssl,requests,urllib3,certifi,idna,charset-normalizer

# (str) The format used to package the app for android: 'apk' or 'aab'
android.package_format = apk

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (bool) Enable AndroidX support
android.androidx = True

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android NDK version to use
android.ndk = r25b

# (list) Permissions
android.permissions = INTERNET

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
bin_dir = ./bin
