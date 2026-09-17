[app]

# (str) Title of your application
title = Nexus App

# (str) Version of the application
version = 0.1

# (str) Package name
package.name = nexusapp

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (list) Source files to include (let it be empty to include all files)
source.dir = .

# (list) Source files to exclude (let it be empty to exclude nothing)
source.exclude_exts = spec

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (str) Supported orientations
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (bool) Skip android SDK license confirmation
android.accept_sdk_license = True
