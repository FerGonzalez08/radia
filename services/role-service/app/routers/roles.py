import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_client import list_users_internal, update_user_role_internal
from app.core.config import ADMIN_ROLE_ID, MENTEE_ROLE_ID, MENTOR_ROLE_ID
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.role import Role
from app.models.role_change_log import RoleChangeLog
from app.schemas.role import RoleChangeLogOut, RoleOut, UserWithRoleOut

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()


@router.get("/users", response_model=list[UserWithRoleOut])
async def list_users(_admin: dict = Depends(require_admin)):
    return await list_users_internal()


@router.get("/audit-log", response_model=list[RoleChangeLogOut])
async def list_audit_log(db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    """HU-AUDIT - Traza de todos los cambios de rol (promover/revertir), mas
    reciente primero, con nombres y roles ya resueltos para el panel de
    administracion (ningun dato tecnico crudo, solo lo que se va a mostrar)."""
    entries = db.query(RoleChangeLog).order_by(RoleChangeLog.changed_at.desc()).all()
    if not entries:
        return []

    users_by_id = {u["id"]: u for u in await list_users_internal()}
    roles_by_id = {str(r.id): r.name for r in db.query(Role).all()}

    def user_info(user_id: uuid.UUID) -> tuple[str, str]:
        user = users_by_id.get(str(user_id))
        if user is None:
            return "Usuario eliminado", "-"
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


@router.post("/{user_id}/promote", response_model=UserWithRoleOut)
async def promote_to_mentor(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    target = await _get_target_user(user_id)

    if target["role_id"] == str(ADMIN_ROLE_ID):
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede reasignar el rol de un administrador")
    if target["role_id"] == str(MENTOR_ROLE_ID):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El usuario ya es mentora")

    updated = await update_user_role_internal(str(user_id), str(MENTOR_ROLE_ID))

    db.add(RoleChangeLog(
        target_user_id=user_id,
        admin_user_id=uuid.UUID(admin["user_id"]),
        previous_role_id=uuid.UUID(target["role_id"]),
        new_role_id=MENTOR_ROLE_ID,
        changed_at=datetime.now(timezone.utc),
    ))
    db.commit()

    return updated


@router.post("/{user_id}/revert", response_model=UserWithRoleOut)
async def revert_to_estudiante(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    target = await _get_target_user(user_id)

    if target["role_id"] == str(ADMIN_ROLE_ID):
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede reasignar el rol de un administrador")
    if target["role_id"] != str(MENTOR_ROLE_ID):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Solo se puede revertir un usuario que actualmente es mentora")

    updated = await update_user_role_internal(str(user_id), str(MENTEE_ROLE_ID))

    db.add(RoleChangeLog(
        target_user_id=user_id,
        admin_user_id=uuid.UUID(admin["user_id"]),
        previous_role_id=MENTOR_ROLE_ID,
        new_role_id=MENTEE_ROLE_ID,
        changed_at=datetime.now(timezone.utc),
    ))
    db.commit()

    # TODO: notificar a Navigation Service para cancelar mentorías activas
    # de este usuario. Pendiente de definir: llamada síncrona vs evento
    # asíncrono (ver decisión arquitectónica en RQF-008). No implementado
    # porque Navigation Service no existe todavía. Este hook se movió aquí
    # desde Auth Service porque la lógica de negocio de reversión ahora
    # vive en Role Service.

    return updated
