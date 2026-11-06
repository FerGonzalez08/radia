"""Administrador de conexiones WebSocket (RQF-016/019): presencia y entrega a varias sesiones."""
import asyncio

from app.core.connection_manager import ConnectionManager


class FakeWS:
    def __init__(self, roto=False):
        self.aceptado, self.recibidos, self.roto = False, [], roto

    async def accept(self):
        self.aceptado = True

    async def send_json(self, payload):
        if self.roto:
            raise RuntimeError("conexión rota")
        self.recibidos.append(payload)


def run(coro):
    return asyncio.run(coro)


def test_connect_acepta_y_registra_la_sesion():
    m, ws = ConnectionManager(), FakeWS()
    run(m.connect("u1", ws))
    assert ws.aceptado and m.is_online("u1") and not m.is_online("u2")


def test_una_persona_puede_tener_varias_pestanas():
    m, a, b = ConnectionManager(), FakeWS(), FakeWS()
    run(m.connect("u1", a))
    run(m.connect("u1", b))
    assert len(m.active_connections["u1"]) == 2


def test_disconnect_solo_informa_ultima_sesion_cuando_ya_no_queda_ninguna():
    m, a, b = ConnectionManager(), FakeWS(), FakeWS()
    run(m.connect("u1", a))
    run(m.connect("u1", b))
    assert m.disconnect("u1", a) is False and m.is_online("u1")
    assert m.disconnect("u1", b) is True and not m.is_online("u1")
    assert "u1" not in m.active_connections


def test_disconnect_de_usuario_desconocido_es_seguro():
    assert ConnectionManager().disconnect("nadie", FakeWS()) is True


def test_send_to_sin_sesiones_devuelve_false():
    assert run(ConnectionManager().send_to("nadie", {"x": 1})) is False


def test_send_to_entrega_a_todas_las_sesiones():
    m, a, b = ConnectionManager(), FakeWS(), FakeWS()
    run(m.connect("u1", a))
    run(m.connect("u1", b))
    assert run(m.send_to("u1", {"x": 1})) is True
    assert a.recibidos == b.recibidos == [{"x": 1}]


def test_una_conexion_rota_no_impide_entregar_a_las_demas_y_se_descarta():
    m, rota, buena = ConnectionManager(), FakeWS(roto=True), FakeWS()
    run(m.connect("u1", rota))
    run(m.connect("u1", buena))
    assert run(m.send_to("u1", {"x": 1})) is True
    assert buena.recibidos == [{"x": 1}] and rota not in m.active_connections["u1"]


def test_si_todas_las_conexiones_estan_rotas_no_se_considera_entregado():
    m, rota = ConnectionManager(), FakeWS(roto=True)
    run(m.connect("u1", rota))
    assert run(m.send_to("u1", {"x": 1})) is False
