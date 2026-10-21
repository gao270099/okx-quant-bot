[app]
title = OKX Quant Master
package.name = okxquantmaster
package.domain = org.quant
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0
# 精简依赖，只保留最核心的库，极大缩短编译时间
requirements = python3,kivy,ccxt,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET

android.api = 33
android.minapi = 21
android.accept_sdk_license = True
