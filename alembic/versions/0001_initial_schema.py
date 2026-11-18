"""create_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-18 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Tabla usuarios
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('apellido', sa.String(length=100), nullable=False),
        sa.Column('correo', sa.String(length=150), nullable=False),
        sa.Column('usuario', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('rol', sa.Enum('ADMINISTRADOR', 'SEGURIDAD', 'SUPERVISOR', name='rolusuario'), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuarios_correo'), 'usuarios', ['correo'], unique=True)
    op.create_index(op.f('ix_usuarios_usuario'), 'usuarios', ['usuario'], unique=True)
    op.create_index(op.f('ix_usuarios_id'), 'usuarios', ['id'], unique=False)

    # 2. Tabla camaras
    op.create_table(
        'camaras',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('ubicacion', sa.String(length=150), nullable=False),
        sa.Column('rtsp_url', sa.String(length=500), nullable=False),
        sa.Column('tipo_fuente', sa.Enum('WEBCAM', 'MP4', 'RTSP', name='tipofuentecamara'), nullable=False),
        sa.Column('estado', sa.Enum('Conectada', 'Desconectada', 'Error', 'Reconectando', name='estadocamara'), nullable=False),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('fps', sa.Integer(), nullable=False, server_default=sa.text('25')),
        sa.Column('resolucion', sa.String(length=20), nullable=True),
        sa.Column('fecha_registro', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('fecha_actualizacion', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_camaras_id'), 'camaras', ['id'], unique=False)

    # 3. Tabla incidentes
    op.create_table(
        'incidentes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('camara_id', sa.Integer(), nullable=True),
        sa.Column('tipo', sa.Enum('Caída', 'Posible agresión', 'Movimiento brusco', 'Persona inmóvil', 'Posible solicitud de auxilio', 'Otro evento sospechoso', name='tipoincidente'), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('nivel_riesgo', sa.Enum('BAJO', 'MEDIO', 'ALTO', 'CRITICO', name='nivelriesgo'), nullable=False),
        sa.Column('confianza', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column('fecha_hora', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('estado', sa.Enum('PENDIENTE', 'EN_REVISION', 'CONFIRMADO', 'DESCARTADO', 'CERRADO', name='estadoincidente'), nullable=False),
        sa.Column('usuario_asignado_id', sa.Integer(), nullable=True),
        sa.Column('es_simulado', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.ForeignKeyConstraint(['camara_id'], ['camaras.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['usuario_asignado_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_incidentes_id'), 'incidentes', ['id'], unique=False)
    op.create_index(op.f('ix_incidentes_camara_id'), 'incidentes', ['camara_id'], unique=False)
    op.create_index(op.f('ix_incidentes_tipo'), 'incidentes', ['tipo'], unique=False)
    op.create_index(op.f('ix_incidentes_fecha_hora'), 'incidentes', ['fecha_hora'], unique=False)
    op.create_index(op.f('ix_incidentes_estado'), 'incidentes', ['estado'], unique=False)
    op.create_index(op.f('ix_incidentes_usuario_asignado_id'), 'incidentes', ['usuario_asignado_id'], unique=False)

    # 4. Tabla alertas
    op.create_table(
        'alertas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incidente_id', sa.Integer(), nullable=False),
        sa.Column('mensaje', sa.Text(), nullable=False),
        sa.Column('prioridad', sa.Enum('BAJA', 'MEDIA', 'ALTA', 'CRITICA', name='prioridadalerta'), nullable=False),
        sa.Column('estado', sa.Enum('ACTIVA', 'CONFIRMADA', 'DESCARTADA', 'CERRADA', name='estadoalerta'), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('fecha_confirmacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_cierre', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usuario_gestion_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['incidente_id'], ['incidentes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_gestion_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_alertas_id'), 'alertas', ['id'], unique=False)
    op.create_index(op.f('ix_alertas_incidente_id'), 'alertas', ['incidente_id'], unique=False)
    op.create_index(op.f('ix_alertas_fecha_creacion'), 'alertas', ['fecha_creacion'], unique=False)
    op.create_index(op.f('ix_alertas_estado'), 'alertas', ['estado'], unique=False)

    # 5. Tabla evidencias
    op.create_table(
        'evidencias',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('incidente_id', sa.Integer(), nullable=False),
        sa.Column('tipo_archivo', sa.Enum('IMAGEN', 'VIDEO', name='tipoevidencia'), nullable=False),
        sa.Column('ruta_archivo', sa.String(length=500), nullable=False),
        sa.Column('tamano_bytes', sa.BigInteger(), nullable=True),
        sa.Column('hash_sha256', sa.String(length=64), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['incidente_id'], ['incidentes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidencias_id'), 'evidencias', ['id'], unique=False)
    op.create_index(op.f('ix_evidencias_incidente_id'), 'evidencias', ['incidente_id'], unique=False)

    # 6. Tabla notificaciones
    op.create_table(
        'notificaciones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('alerta_id', sa.Integer(), nullable=True),
        sa.Column('mensaje', sa.Text(), nullable=False),
        sa.Column('canal', sa.Enum('WEBSOCKET', 'EMAIL', name='canalnotificacion'), nullable=False),
        sa.Column('leida', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('fecha_envio', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['alerta_id'], ['alertas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notificaciones_id'), 'notificaciones', ['id'], unique=False)
    op.create_index(op.f('ix_notificaciones_usuario_id'), 'notificaciones', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_notificaciones_alerta_id'), 'notificaciones', ['alerta_id'], unique=False)

    # 7. Tabla auditoria
    op.create_table(
        'auditoria',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('accion', sa.String(length=50), nullable=False),
        sa.Column('entidad', sa.String(length=50), nullable=False),
        sa.Column('entidad_id', sa.Integer(), nullable=True),
        sa.Column('detalles', sa.Text(), nullable=True),
        sa.Column('ip_origen', sa.String(length=45), nullable=True),
        sa.Column('fecha_hora', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auditoria_id'), 'auditoria', ['id'], unique=False)
    op.create_index(op.f('ix_auditoria_usuario_id'), 'auditoria', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_auditoria_accion'), 'auditoria', ['accion'], unique=False)
    op.create_index(op.f('ix_auditoria_entidad'), 'auditoria', ['entidad'], unique=False)
    op.create_index(op.f('ix_auditoria_fecha_hora'), 'auditoria', ['fecha_hora'], unique=False)


def downgrade() -> None:
    op.drop_table('auditoria')
    op.drop_table('notificaciones')
    op.drop_table('evidencias')
    op.drop_table('alertas')
    op.drop_table('incidentes')
    op.drop_table('camaras')
    op.drop_table('usuarios')
