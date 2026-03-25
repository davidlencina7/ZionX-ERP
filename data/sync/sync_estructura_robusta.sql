-- Script SQL robusto para sincronización de estructura y RLS
-- Ejecuta cada bloque por separado para evitar errores de columnas ya existentes o renombradas

-- USUARIOS
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='usuarios' AND column_name='nombre')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='usuarios' AND column_name='nombre_completo') THEN
        EXECUTE 'ALTER TABLE usuarios RENAME COLUMN nombre TO nombre_completo';
    END IF;
END$$;

ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS rol VARCHAR(50) DEFAULT 'usuario';
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tema_preferido VARCHAR(20) DEFAULT 'light';
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS fecha_creacion TIMESTAMP;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_acceso TIMESTAMP;

-- Columnas adicionales confirmadas como estándar
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS fecha TIMESTAMP;

-- PRODUCTOS
ALTER TABLE productos ADD COLUMN IF NOT EXISTS costo_unitario NUMERIC;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS margen_porcentaje NUMERIC;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS precio_sugerido NUMERIC;
-- Si 'precio' es el campo correcto, renómbralo:
-- DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='productos' AND column_name='precio') AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='productos' AND column_name='precio_sugerido') THEN EXECUTE 'ALTER TABLE productos RENAME COLUMN precio TO precio_sugerido'; END IF; END$$;

ALTER TABLE productos ADD COLUMN IF NOT EXISTS especificaciones TEXT;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS precio NUMERIC;
ALTER TABLE productos ADD COLUMN IF NOT EXISTS fecha TIMESTAMP;

-- COMPRAS
ALTER TABLE compras ADD COLUMN IF NOT EXISTS producto_id INTEGER;
ALTER TABLE compras ADD COLUMN IF NOT EXISTS cantidad NUMERIC;
ALTER TABLE compras ADD COLUMN IF NOT EXISTS costo_unitario NUMERIC;
ALTER TABLE compras ADD COLUMN IF NOT EXISTS fecha TIMESTAMP;
ALTER TABLE compras ADD COLUMN IF NOT EXISTS mes_contable VARCHAR(20);

ALTER TABLE compras ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);

-- VENTAS
ALTER TABLE ventas ADD COLUMN IF NOT EXISTS producto_id INTEGER;
ALTER TABLE ventas ADD COLUMN IF NOT EXISTS cantidad NUMERIC;
ALTER TABLE ventas ADD COLUMN IF NOT EXISTS precio_unitario NUMERIC;
ALTER TABLE ventas ADD COLUMN IF NOT EXISTS costo_unitario NUMERIC;
ALTER TABLE ventas ADD COLUMN IF NOT EXISTS ganancia_unitaria NUMERIC;
ALTER TABLE ventas ADD COLUMN IF NOT EXISTS fecha TIMESTAMP;
ALTER TABLE ventas ADD COLUMN IF NOT EXISTS forma_pago VARCHAR(50);
ALTER TABLE ventas ADD COLUMN IF NOT EXISTS mes_contable VARCHAR(20);

ALTER TABLE ventas ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);

-- GASTOS
ALTER TABLE gastos ADD COLUMN IF NOT EXISTS fecha_registro TIMESTAMP;
-- Si 'descripcion' es equivalente a 'notas':
-- DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='gastos' AND column_name='descripcion') AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='gastos' AND column_name='notas') THEN EXECUTE 'ALTER TABLE gastos RENAME COLUMN descripcion TO notas'; END IF; END$$;

ALTER TABLE gastos ADD COLUMN IF NOT EXISTS descripcion TEXT;
ALTER TABLE gastos ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
ALTER TABLE gastos ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);

-- ACTIVOS
ALTER TABLE activos ADD COLUMN IF NOT EXISTS activo BOOLEAN DEFAULT TRUE;
ALTER TABLE activos ADD COLUMN IF NOT EXISTS usuario_id INTEGER;
ALTER TABLE activos ADD COLUMN IF NOT EXISTS fecha_registro TIMESTAMP;

ALTER TABLE activos ADD COLUMN IF NOT EXISTS vida_util_anos INTEGER;
ALTER TABLE activos ADD COLUMN IF NOT EXISTS estado VARCHAR(50);
ALTER TABLE activos ADD COLUMN IF NOT EXISTS user_id INTEGER;
ALTER TABLE activos ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
ALTER TABLE activos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE activos ADD COLUMN IF NOT EXISTS valor NUMERIC;

-- ACCOUNTS
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS fecha_registro TIMESTAMP;

ALTER TABLE accounts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS fecha TIMESTAMP;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS type VARCHAR(50);

-- MOVIMIENTOS CONTABLES
ALTER TABLE movimientos_contables ADD COLUMN IF NOT EXISTS debe NUMERIC;
ALTER TABLE movimientos_contables ADD COLUMN IF NOT EXISTS haber NUMERIC;
ALTER TABLE movimientos_contables ADD COLUMN IF NOT EXISTS descripcion TEXT;
ALTER TABLE movimientos_contables ADD COLUMN IF NOT EXISTS nombre VARCHAR(255);
ALTER TABLE movimientos_contables ADD COLUMN IF NOT EXISTS fecha TIMESTAMP;
ALTER TABLE movimientos_contables ADD COLUMN IF NOT EXISTS cuenta_id INTEGER;

-- JOURNAL ENTRIES
ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS fecha TIMESTAMP;
ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS descripcion TEXT;

-- JOURNAL LINES
ALTER TABLE journal_lines ADD COLUMN IF NOT EXISTS debe NUMERIC;
ALTER TABLE journal_lines ADD COLUMN IF NOT EXISTS haber NUMERIC;

-- POLÍTICAS RLS DE EJEMPLO
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE compras ENABLE ROW LEVEL SECURITY;
ALTER TABLE ventas ENABLE ROW LEVEL SECURITY;
ALTER TABLE gastos ENABLE ROW LEVEL SECURITY;
ALTER TABLE activos ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

-- Asegura que el rol 'admin' exista antes de crear la política RLS
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin') THEN
    CREATE ROLE admin;
  END IF;
END$$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'admin_edit_all_usuarios') THEN
    CREATE POLICY admin_edit_all_usuarios ON usuarios
      FOR ALL
      TO admin
      USING (true)
      WITH CHECK (true);
  END IF;
END$$;
-- Repite para cada tabla y ajusta los roles según tu sistema
