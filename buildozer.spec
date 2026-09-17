[app]

# (str) Title of your application
title = Meu App Kivy

# (str) Package name
package.name = nexusapp

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (str) Source directory where the main.py file lives
source.dir = .

# (str) Application versioning (OBRIGATÓRIO)
version = 0.1

# (list) Source files to include (let it empty to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
requirements = python3,kivy,sdl2,sdl2_image,sdl2_mixer,libffi,openssl

# (str) Supported orientations
orientation = portrait

# (list) The android target API
android.api = 34

# (int) Minimum API your APK will support
android.minapi = 21

# (list) Architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (str) The NDK version to use
android.ndk = 25b
