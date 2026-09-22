[app]

# (str) Title of your application
title = Nexus

# (str) Package name
package.name = nexusquantum

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (list) Source files to include (incluindo json para o arquivo de configuração seguro)
source.include_exts = py,png,jpg,kv,atlas,json,enc

# (list) Application requirements
requirements = python3,kivy,plyer,requests,urllib3,idna,certifi,pyttsx3

# (str) Supported orientations
orientation = portrait

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,RECORD_AUDIO,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = no, 1 = yes)
warn_on_root = 1
