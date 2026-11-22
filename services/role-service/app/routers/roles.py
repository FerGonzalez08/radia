import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth_client import (
    cancel_mentor_mentorships_internal,
    list_users_internal,
    list_users_page_internal,
    update_user_role_internal,
)
from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID
from app.core.database import get_db
from app.core.deps import get_current_session, require_admin
from app.models.role import Role
from app.models.role_change_log import RoleChangeLog
from app.schemas.role import RoleChangeLogOut, RoleOut, UserWithRoleOut

router = APIRouter(prefix="/roles", tags=["roles"])
logger = logging.getLogger(__name__)


@router.get("", response_model=list[RoleOut])
async def list_roles(db: Session = Depends(get_db), _session: dict = Depends(get_current_session)):
    """Acceso: cualquier usuaria autenticada (Mentee, Mentora o Administradora)."""
    return db.query(Role).all()


@router.get("/users", response_model=list[UserWithRoleOut])
async def list_users(
    q: str | None = Query(default=None, max_length=100, description="Texto a buscar en nombre o correo"),
    role_id: uuid.UUID | None = Query(default=None, description="Filtra por rol"),
    limit: int | None = Query(default=None, ge=1, le=500, description="Máximo de filas; sin valor devuelve todas"),
    offset: int = Query(default=0, ge=0),
    _admin: dict = Depends(require_admin),
):
    """Lista las usuarias con su rol. Sin parámetros devuelve todas; con q, role_id, limit y offset el filtro y la
    paginación se resuelven en la base de datos (TC-NFR-09).

    Acceso: rol Administradora.
    """
    return await list_users_page_internal(q, str(role_id) if role_id else None, limit, offset)


@router.get("/audit-log", response_model=list[RoleChangeLogOut])
async def list_audit_log(db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    """HU-AUDIT - Traza de todos los cambios de rol (promover/revertir), mas
    reciente primero, con nombres y roles ya resueltos para el panel de
    administracion (ningun dato tecnico crudo, solo lo que se va a mostrar).

    Acceso: rol Administradora.
    """
    entries = db.query(RoleChangeLog).order_by(RoleChangeLog.changed_at.desc()).all()
    if not entries:
        return []

    users_by_id = {u["id"]: u for u in await list_users_internal()}
    roles_by_id = {str(r.id): r.name for r in db.query(Role).all()}

    def user_info(user_id: uuid.UUID) -> tuple[str, str]:
        user = users_by_id.get(str(user_id))
        if user is None:
            return "Usuario desactivado", "-"
        if not user.get("is_active", True):
            return "Usuario desactivado", user["email"]
        return user["nombre"], user["email"]

    result = []
    for entry in entries:
        admin_nombre, admin_email = user_info(entry.admin_user_id)
        target_nombre, target_email = user_info(entry.target_user_id)
        result.append(
            RoleChangeLogOut(
                id=entry.id,
                changed_at=entry.changed_at,
                admin_user_id=entry.admin_user_id,
                admin_nombre=admin_nombre,
                admin_email=admin_email,
                target_user_id=entry.target_user_id,
                target_nombre=target_nombre,
                target_email=target_email,
                previous_role=roles_by_id.get(str(entry.previous_role_id), "Desconocido"),
                new_role=roles_by_id.get(str(entry.new_role_id), "Desconocido"),
            )
        )
    return result


async def _get_target_user(user_id: uuid.UUID) -> dict:
    users = await list_users_internal()
    target = next((u for u in users if u["id"] == str(user_id)), None)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
    return target


async def _cambiar_rol_con_auditoria(
    db: Session, admin: dict, user_id: uuid.UUID, rol_anterior: uuid.UUID, rol_nuevo: uuid.UUID, antes=None,
) -> dict:
    """Cambia el rol y registra la auditoría de forma consistente (TC-ROL-03): nunca queda un rol cambiado sin su registro.

    La fila de auditoría se escribe primero (sin confirmar), luego se cambia el rol en Auth Service y al final se
    confirma. Si el cambio de rol falla, no queda registro. Si falla la confirmación, se restituye el rol anterior.
    """
    db.add(RoleChangeLog(
        target_user_id=user_id,
        admin_user_id=uuid.UUID(admin["user_id"]),
        previous_role_id=rol_anterior,
        new_role_id=rol_nuevo,
        changed_at=datetime.now(timezone.utc),
    ))
    db.flush()
    try:
        if antes is not None:
            await antes()
        updated = await update_user_role_internal(str(user_id), str(rol_nuevo))
    except Exception:
        db.rollback()
        raise
    try:
        db.commit()
    except Exception:
        db.rollback()
        try:
            await update_user_role_internal(str(user_id), str(rol_anterior))
        except Exception:
            logger.critical("Rol de %s cambiado sin registro de auditoría y sin poder restituirlo", user_id)
        raise
    return updated


@router.post("/{user_id}/promote", response_model=UserWithRoleOut)
async def promote_to_mentor(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """Acceso: rol Administradora."""
    target = await _get_target_user(user_id)

    if target["role_id"] == str(ADMIN_ROLE_ID):
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede reasignar el rol de un administrador")
    if target["role_id"] == str(MENTOR_ROLE_ID):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El usuario ya es mentora")

    return await _cambiar_rol_con_auditoria(db, admin, user_id, uuid.UUID(target["role_id"]), MENTOR_ROLE_ID)


@router.post("/{user_id}/revert", response_model=UserWithRoleOut)
async def revert_to_estudiante(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """Acceso: rol Administradora."""
    target = await _get_target_user(user_id)

    if target["role_id"] == str(ADMIN_ROLE_ID):
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede reasignar el rol de un administrador")
    if target["role_id"] != str(MENTOR_ROLE_ID):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se puede revertir un usuario que actualmente es mentora")

    # TC-ROL-04: al revertir a una mentora se cancelan antes sus mentorías pendientes y confirmadas (el chat se bloquea).
    return await _cambiar_rol_con_auditoria(
        db, admin, user_id, MENTOR_ROLE_ID, MENTEE_ROLE_ID,
        antes=lambda: cancel_mentor_mentorships_internal(str(user_id)),
    )
