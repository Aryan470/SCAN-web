import scan_web
import os

try:
    port = os.environ["PORT"]
except KeyError:
    port = 7000

scan_web.create_app(port).run()