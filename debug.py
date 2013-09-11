DEBUG = False
try:
    import os
    if os.environ['DEBUG'] == '1':
        DEBUG = True
except:
    pass

