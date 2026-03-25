import sqlite3

# Datos del usuario ilencina
usuario = {
    'id': 2,
    'username': 'ilencina',
    'password_hash': '$2b$12$x70qg2bprb5j.KQSfczyhuvIIC4ZRWtcW0cDv3dGRShnvHy2sJL3m',
    'nombre_completo': 'Iván Lencina',
    'email': 'ilencina@piupiu.local',
    'rol': 'admin',
    'activo': 1,
    'tema_preferido': 'dark',
    'fecha_creacion': '2026-02-13 13:54:22',
}


# Intentar insertar o actualizar el usuario ilencina
c.execute('''
    INSERT INTO usuarios (id, username, password_hash, nombre_completo, email, rol, activo, tema_preferido, fecha_creacion)
    VALUES (:id, :username, :password_hash, :nombre_completo, :email, :rol, :activo, :tema_preferido, :fecha_creacion)
    ON CONFLICT(id) DO UPDATE SET
        username=excluded.username,
        password_hash=excluded.password_hash,
        nombre_completo=excluded.nombre_completo,
        email=excluded.email,
        rol=excluded.rol,
        activo=excluded.activo,
        tema_preferido=excluded.tema_preferido,
        fecha_creacion=excluded.fecha_creacion
''', usuario)

print('Usuario ilencina insertado o actualizado correctamente.')
