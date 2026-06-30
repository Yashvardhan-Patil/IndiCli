import os

dirs = [
    'app',
    'app/core',
    'app/db',
    'app/models',
    'app/services',
    'app/services/forecasting',
    'app/services/simulation',
    'app/services/analytics',
    'app/services/harmonization',
    'app/api',
    'app/api/routes',
]

for d in dirs:
    p = os.path.join(d, '__init__.py')
    with open(p, 'wb') as f:
        f.write(b'')
    nb = open(p, 'rb').read().count(b'\x00')
    print(f'{p}: null_bytes={nb}')
print('All __init__.py files written.')
