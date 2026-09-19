[app]

# (str) Title of your application
title = Nexus Quantum

# (str) Package name
package.name = nexusquantum

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (list) Source files to include (let it include python files, json, enc, etc.)
source.include_exts = py,png,jpg,kv,atlas,json,enc

# (list) Application requirements
# Certifique-se de incluir requests, urllib3, idna, certifi e jnius para internet e voz funcionarem
requirements = python3,kivy,requests,urllib3,idna,certifi,jnius

# (str) Supported orientations
orientation = portrait

# (list) Permissions
# Essencial para garantir acesso à Internet e ao Microfone
android.permissions = INTERNET,ACCESS_NETWORK_STATE,RECORD_AUDIO

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = Z, 1 = yes)
warn_on_root = 1
