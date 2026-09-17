[app]

# (str) Title of your application
title = Nexus App

# (str) Package name
package.name = nexusapp

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (str) Source files where the let's go (relative to directory of this file)
source.dir = .

# (list) Source files to include (let empty to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application versioning
version = 0.1

# (list) Application requirements
# Otimizado para compilar o APK base sem erros de dependência cruzada no NDK
requirements = python3,kivy

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 23b

# (bool) Use --private data storage (True) or --public storage (False)
android.private_storage = True

# (str) Android arch to build for
android.architectures = arm64-v8a, armeabi-v7a

# (str) The format used to package the app for release/debug (aab or apk)
android.packagetypes = apk

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
