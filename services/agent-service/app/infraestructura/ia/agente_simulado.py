"""Proveedor local para probar el flujo conversacional sin servicios externos."""

from app.dominios.conversacion.mensajes import (
    RecursoConversacional,
    RespuestaConversacion,
    SolicitudConversacion,
)


class AgenteConversacionalSimulado:
    """Genera orientación determinista, sin claves ni consumo de modelos externos."""

    nombre_proveedor = "simulado"

    def responder(self, solicitud: SolicitudConversacion) -> RespuestaConversacion:
        """Ofrece una respuesta básica a partir de palabras del mensaje."""
        mensaje = solicitud.mensaje.lower()
        if "program" in mensaje or "código" in mensaje:
            recurso = RecursoConversacional(
                titulo="Guía simulada de programación paso a paso",
                descripcion="Practica la descomposición de problemas en pasos pequeños.",
            )
            respuesta = (
                "Puedes comenzar por dividir el problema en pasos pequeños y practicar "
                "cada uno con ejemplos sencillos."
            )
        elif "dato" in mensaje or "base" in mensaje:
            recurso = RecursoConversacional(
                titulo="Guía simulada de fundamentos de datos",
                descripcion="Repasa conceptos básicos de datos y bases de datos con ejercicios cortos.",
            )
            respuesta = (
                "Una opción es repasar los fundamentos de datos con ejercicios cortos y "
                "anotar las dudas que aparezcan durante la práctica."
            )
        else:
            recurso = RecursoConversacional(
                titulo="Guía simulada de aprendizaje autónomo",
                descripcion="Organiza una meta pequeña, practica y revisa lo aprendido.",
            )
            respuesta = (
                "Puedes elegir una meta pequeña de aprendizaje, practicarla de forma gradual "
                "y buscar apoyo académico cuando lo necesites."
            )

        return RespuestaConversacion(respuesta=respuesta, recursos=(recurso,))
