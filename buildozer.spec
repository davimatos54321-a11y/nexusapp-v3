[app]

# (str) Title of your application
title = NexusQuantum

# (str) Package name
package.name = nexusquantum

# (str) Package domain (needed for android packaging)
package.domain = org.nexus

# (list) Source files to include (let it empty to include all files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusion patterns relative to the root directory
source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let it empty to include all files)
source.exclude_exts = spec

# (list) List of directory to exclude from source files
source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*~

# (str) Application versioning
version = 0.1

# (list) Application requirements
# Requisitos limpos para rodar o Kivy e o motor de requisições de rede sem travar o APK
requirements = python3,kivy,requests,urllib3,certifi,idna,charset-normalizer

# (str) Custom source folders for requirements
#requirements.source.kivy = ../../../kivy

# (list) Permissions
# Liberado o acesso à rede para permitir as chamadas à API-Football
android.permissions = INTERNET

# (list) Supported orientations
orientation = portrait

# (list) List of service to declare
#services = 

#
# OSX Specific
#

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color
#presplash.color = #FFFFFF

# (list) List of extra java jar files to add
#android.add_jars = foo.bar,bar.baz

# (list) List of Java files to add to the android project (classpath, sources)
#android.add_src =

# (list) List of Client intents
#android.intent_filters = 

# (str) Android AAR archive to add
#android.add_aars =

# (list) Gradle dependencies to add
#android.add_gradle_dependencies =

# (bool) Use AndroidX
android.androidx = true

# (str) The format used to package the app for release ('aab' or 'apk')
android.package_format = apk

[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = C, 2 = Python)
#warn_root = 1

# (str) Path to build artifact, default to the root directory of the buildozer.spec
#bin_dir = ./bin

# (str) The internationalization support, boolean
#android.api = 33
#android.minapi = 21
