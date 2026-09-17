[app]

# (str) Title of your application
title = Meu App Kivy

# (str) Package name
package.name = nexusapp

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (list) Source files to include (let it empty to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Application requirements
# (Certifique-se de incluir as dependências do seu projeto aqui)
requirements = python3,kivy,sdl2,sdl2_image,sdl2_mixer,libffi,openssl

# (str) Supported orientations
orientation = portrait

# (list) The android target API, should be 34 for modern Google Play requirements
android.api = 34

# (int) Minimum API your APK will support
android.minapi = 21

# (list) Architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (str) The NDK version to use. Fixado no 25b para estabilidade total do libffi/tramp.c
android.ndk = 25b

# (bool) Enable FULL autotools/cmake-based packages cleaning if needed
# android.skip_update = False
