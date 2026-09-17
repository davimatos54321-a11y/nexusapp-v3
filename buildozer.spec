[app]

# (str) Title of your application
title = Nexus App

# (str) Package name
package.name = nexusapp

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (list) Source files to include (let it blank to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let it blank to exclude none)
#source.exclude_exts = spec

# (list) List of directory to exclude (let it blank to exclude none)
#source.exclude_dirs = tests, bin

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,openssl,requests,urllib3,certifi,idna,charset-normalizer

# (list) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.dir = ../my_custom_source

# (list) Permissions
#android.permissions = INTERNET

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Supported orientations
# Valid options are: landscape, portrait, reverse-landscape, reverse-portrait
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# OSX Specific
#

#
# PDF icon (OSX)
#

# (str) The format used to package the app for android: 'apk' or 'aab'
android.package_format = apk

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Preslash for the Android sdk, if empty, it will be automatically downloaded.
#android.sdk_path =

# (string) 'android-ndk' path or downloading
#android.ndk_path =

# (bool) Enable AndroidX support
android.androidx = True

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android NDK version to use
android.ndk = r25b

# (bool) Use --private data storage (True) or --dir public storage (False)
#android.private_storage = True

# (list) Permissions
android.permissions = INTERNET

# (list) Certifications
#android.manifest.additions = <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

# (str) python-for-android branch to use
#android.branch = master

# (str) p4a git clone to use
#android.p4a_dir =

# (str) Working directory for p4a
#android.build_dir = .build_dir

# (list) The Android archs to build for,, and other choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) Del space between the end of the text and the bottom of the screen on android devices
#android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = Z, 1 = warn)
warn_on_root = 1

# (str) Path to build artifact, output of the build
bin_dir = ./bin

# (int) Number of processes to use for parallel compilation
# 0 means auto-detect
build_number = 0
