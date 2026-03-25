import os

# Buscar recursivamente todos los archivos .py que contengan 'DATABASE_PATH'
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if 'DATABASE_PATH' in line:
                        print(f"{path}:{i}: {line.strip()}")
