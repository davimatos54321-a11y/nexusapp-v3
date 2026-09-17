[app]

# (str) Title of your application
title = Nexus App

# (str) Package name
package.name = nexusapp

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (list) Source files to include (let it be empty to include all files)
source.dir = .

# (list) Source files to exclude (let it be empty to exclude nothing)
source.exclude_exts = spec

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (bool) Skip android SDK license confirmation
android.accept_sdk_license = True

# (str) Android NDK version to use
android.ndk = 25b

# (int) Target Android API, should be as high as possible.
android.api = 33
