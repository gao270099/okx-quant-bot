[app]
title = OKX Quant Master
package.name = okxquantmaster
package.domain = org.quant
source.dir = .
source.include_exts = py,png,jpg,kv
version = 1.0
requirements = python3,kivy,ccxt,certifi,urllib3,charset-normalizer,idna,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET

# 锁定稳定版本，避免 SDK 37 授权报错
android.api = 33
android.minapi = 21

# 自动接受 Android SDK 许可证协议
android.accept_sdk_license = True
