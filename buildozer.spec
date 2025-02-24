[app]
# (str) Title of your application
title = AI Caddy

# (str) Package name
package.name = ai_caddy

# (str) Package domain (needed for android/ios packaging)
package.domain = org.yourdomain

source.dir = /home/jackmehoff/Golf-APP
# (str) Source code where the main.py is located
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
requirements = python3,kivy,requests,pyjnius

# (str) Icon of the application
icon.filename = /home/jackmehoff/Golf-APP/images/APP_Icon.png

# (str) Supported orientation (one of: landscape, portrait, all)
orientation = portrait

[buildozer]
# (int) Log level (0 = error only, 1 = warning, 2 = info, 3 = debug, 4 = trace)
log_level = 2

# (bool) Warn on root access
warn_on_root = 1
