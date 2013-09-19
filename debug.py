DEBUG       = False
BATCH       = False

try:
    import os
    if 'DEBUG' in os.environ:
        DEBUG = True
    if 'BATCH' in os.environ:
        BATCH = True
except:
    pass
