import sys
import os

INTERP = "/home/niraulakunjan/virtualenv/scl.sajilocode.com/3.12/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

PROJECT_HOME = "/home/niraulakunjan/scl.sajilocode.com"
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolms.settings")

from schoolms.wsgi import application
