"""Política de contraseña (HU001): mínimo 8 caracteres y que sea alfanumérica (al menos una letra y un número)."""

PASSWORD_POLICY_MESSAGE = "La contraseña debe tener mínimo 8 caracteres alfanuméricos"


def validate_password_policy(value: str) -> str:
    tiene_letra = any(c.isalpha() for c in value)
    tiene_numero = any(c.isdigit() for c in value)
    if len(value) < 8 or not tiene_letra or not tiene_numero:
        raise ValueError(PASSWORD_POLICY_MESSAGE)
    return value
