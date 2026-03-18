[app]
title = Sistem Güncelleme
package.name = shinsoo
package.domain = com.shinsoo

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,m4a

version = 1.0

requirements = python3,kivy==2.2.1,requests,certifi,urllib3,charset-normalizer,idna

orientation = portrait
fullscreen = 1

android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = False

source.include_patterns = music.m4a

[buildozer]
log_level = 2
warn_on_root = 1
