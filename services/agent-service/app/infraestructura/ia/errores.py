"""Errores controlados de los proveedores de inteligencia artificial."""


class ConfiguracionProveedorInvalidaError(ValueError):
    """Indica que faltan o son inválidos los datos de un proveedor externo."""


class ProveedorIAIndisponibleError(RuntimeError):
    """Indica que el proveedor no pudo responder sin revelar detalles sensibles."""
