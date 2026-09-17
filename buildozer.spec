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
version = 1.0

# (list) Application requirements — Versão travada para evitar falhas no Cython/SDL2
requirements = python3,kivy==2.3.0,sdl2

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 34

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version
android.ndk = 27b

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
