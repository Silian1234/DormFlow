[app]
title = DormFlow
package.name = dormflow
package.domain = org.dormflow

source.dir = ../..
source.include_exts = py,kv,png,jpg,jpeg,ttf,json,txt
source.exclude_dirs = .git,__pycache__,.pytest_cache,.venv,.venv310,venv,backend,docs,prototype,assets/ios,apps/android/.buildozer,apps/android/bin,apps/ios,tests,qa-results

presplash.filename = ../../assets/android/presplash.png
icon.filename = ../../assets/android/icon.png

version = 1.0.0

requirements = python3,kivy
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,CAMERA
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.presplash_color = #F5EFE4

log_level = 2

[buildozer]
warn_on_root = 1
