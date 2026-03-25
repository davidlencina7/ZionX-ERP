"""
Modelos para contabilidad
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

from backend.utils.enums import AccountType, AccountNature, MovementType, JournalEntryType


@dataclass
class Gasto:
    """Representa un gasto registrado"""
    concepto: str
    monto: float
    categoria: str
    fecha: date
    mes_contable: str
    id: Optional[int] = None
    usuario_id: Optional[int] = None
    notas: Optional[str] = None
    fecha_registro: Optional[datetime] = None
    
    def __repr__(self) -> str:
        return f"Gasto(id={self.id}, concepto='{self.concepto}', monto=${self.monto:.2f})"


@dataclass
class Activo:
    """Representa un activo registrado"""
    nombre: str
    valor_adquisicion: float
    fecha_adquisicion: date
    categoria: str
    id: Optional[int] = None
    descripcion: Optional[str] = None
    vida_util_meses: Optional[int] = None
    valor_residual: float = 0.0
    depreciacion_mensual: float = 0.0
    activo: bool = True
    usuario_id: Optional[int] = None
    fecha_registro: Optional[datetime] = None
    
    def calcular_depreciacion_mensual(self) -> float:
        """Calcular depreciación mensual lineal"""
        if self.vida_util_meses and self.vida_util_meses > 0:
            return (self.valor_adquisicion - self.valor_residual) / self.vida_util_meses
        return 0.0
    
    def __repr__(self) -> str:
        return f"Activo(id={self.id}, nombre='{self.nombre}', valor=${self.valor_adquisicion:.2f})"


@dataclass
class MovimientoContable:
    """Representa un movimiento en el calendario contable"""
    mes_contable: str
    tipo: str  # 'ingreso', 'egreso', 'inventario'
    categoria: str
    concepto: str
    monto: float
    fecha_movimiento: date
    id: Optional[int] = None
    referencia_tabla: Optional[str] = None
    referencia_id: Optional[int] = None
    usuario_id: Optional[int] = None
    fecha_registro: Optional[datetime] = None
    
    def __repr__(self) -> str:
        return f"MovimientoContable(mes='{self.mes_contable}', tipo='{self.tipo}', monto=${self.monto:.2f})"


@dataclass
class Account:
    """Representa una cuenta del plan de cuentas contable"""
    code: str  # Código jerárquico (ej: "1.1.01")
    name: str  # Nombre de la cuenta (ej: "Caja")
    account_type: AccountType  # activo, pasivo, patrimonio, ingreso, gasto
    nature: AccountNature  # deudora, acreedora
    id: Optional[int] = None
    subtype: Optional[str] = None  # "corriente", "no_corriente"
    parent_id: Optional[int] = None  # Para jerarquías de cuentas
    active: bool = True
    description: Optional[str] = None
    fecha_registro: Optional[datetime] = None
    
    def calcular_balance(self, conn) -> float:
        """
        Calcular balance dinámicamente desde journal_lines
        Balance = DEBE - HABER (para cuentas deudoras)
        Balance = HABER - DEBE (para cuentas acreedoras)
        """
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT SUM(debit), SUM(credit) 
               FROM journal_lines 
               WHERE account_id = %s''',
            (self.id,)
        )
        row = cursor.fetchone()
        debe = row[0] if row[0] else 0.0
        haber = row[1] if row[1] else 0.0
        
        if self.nature == AccountNature.DEUDORA:
            return debe - haber
        else:
            return haber - debe
    
    def __repr__(self) -> str:
        return f"Account(code='{self.code}', name='{self.name}', type={self.account_type.value})"


@dataclass
class JournalEntry:
    """Representa un asiento contable (cabecera)"""
    date: datetime
    description: str
    entry_type: JournalEntryType
    id: Optional[int] = None
    reference_table: Optional[str] = None  # "ventas", "compras", "gastos"
    reference_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def __repr__(self) -> str:
        return f"JournalEntry(id={self.id}, date={self.date}, type={self.entry_type.value})"


@dataclass
class JournalLine:
    """Representa una línea de un asiento contable (detalle)"""
    journal_entry_id: int
    account_id: int
    debit: float = 0.0
    credit: float = 0.0
    id: Optional[int] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validar que solo uno de debit/credit tenga valor"""
        if self.debit > 0 and self.credit > 0:
            raise ValueError("Una línea no puede tener DEBE y HABER simultáneamente")
        if self.debit < 0 or self.credit < 0:
            raise ValueError("DEBE y HABER deben ser valores positivos")
    
    def __repr__(self) -> str:
        return f"JournalLine(account_id={self.account_id}, debit={self.debit:.2f}, credit={self.credit:.2f})"


@dataclass
class InventoryMovement:
    """Representa un movimiento de inventario valorizado"""
    producto_id: int
    movement_type: MovementType  # entrada, salida, ajuste
    cantidad: float
    costo_unitario: float  # Costo promedio ponderado al momento del movimiento
    fecha: datetime
    id: Optional[int] = None
    reference_table: Optional[str] = None  # "compras", "ventas"
    reference_id: Optional[int] = None
    descripcion: Optional[str] = None
    stock_anterior: Optional[float] = None
    stock_nuevo: Optional[float] = None
    costo_promedio_anterior: Optional[float] = None
    costo_promedio_nuevo: Optional[float] = None
    
    @property
    def valor_total(self) -> float:
        """Valor total del movimiento"""
        return self.cantidad * self.costo_unitario
    
    def __repr__(self) -> str:
        return (f"InventoryMovement(producto_id={self.producto_id}, "
                f"type={self.movement_type.value}, qty={self.cantidad}, "
                f"cost=${self.costo_unitario:.2f})")
