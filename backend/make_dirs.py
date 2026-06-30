import os
for d in ['models', 'uploads', 'cache', 'logs']:
    full = os.path.abspath(d)
    os.makedirs(full, exist_ok=True)
    print(d, '->', full, '| exists:', os.path.exists(full))
