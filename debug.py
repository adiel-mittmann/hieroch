DEBUG       = False
BATCH       = False

try:
    import os
    if os.environ.has_key('DEBUG'):
        DEBUG = True
    if os.environ.has_key('BATCH'):
        BATCH = True
except:
    pass
