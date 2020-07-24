import scan_web
import os

try:
    port = os.environ["PORT"]
except KeyError:
    port = 7000

scan_web.create_app().run(host="0.0.0.0", debug=True, port=port)
