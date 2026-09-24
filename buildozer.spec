[app]
title = Jazz Trainer
package.name = jazztrainer
package.domain = org.jazztrainer

source.dir = .
source.include_exts = py,png,jpg

version = 1.0

requirements = python3,kivy,pygame

orientation = portrait
fullscreen = 1

android.presplash = splash.png
android.icon = icon.png

android.api = 31
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True

android.permissions = INTERNET,WAKE_LOCK
android.target_api = 31
android.archs = arm64-v8a,armeabi-v7a
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
