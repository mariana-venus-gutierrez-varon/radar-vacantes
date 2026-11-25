"""Pruebas de las reglas de filtrado con vacantes inventadas.

No usan internet: cada vacante de prueba imita el formato real de Himalayas.
Uso:  python pruebas.py
"""

import json
import time
import unittest

import filtros

with open("config.json", encoding="utf-8") as archivo:
    CONFIG = json.load(archivo)

FUTURO = int(time.time() + 30 * 86400)  # Vence en 30 días (segundos, como la API real).
RELLENO = " Our team works across many countries and values clear communication." * 5


def vacante(**cambios):
    """Crea una vacante base que pasa todas las reglas, con los cambios pedidos."""
    base = {
        "guid": "base",
        "title": "Junior Financial Analyst",
        "companyName": "Empresa Ejemplo",
        "employmentType": "Full Time",
        "seniority": ["Entry-level"],
        "locationRestrictions": ["Colombia", "Mexico"],
        "timezoneRestrictions": [],
        "description": "<p>We need 1+ years of experience with Excel.</p>" + RELLENO,
        "expiryDate": FUTURO,
        "applicationLink": "https://himalayas.app/companies/ejemplo/jobs/analyst",
    }
    base.update(cambios)
    return base


class PruebasReglas(unittest.TestCase):

    def motivo(self, v):
        pasan, descartadas = filtros.evaluar([v], CONFIG)
        return descartadas[0][1] if descartadas else None

    def test_vacante_buena_pasa(self):
        self.assertIsNone(self.motivo(vacante()))

    def test_worldwide_pasa(self):
        self.assertIsNone(self.motivo(vacante(locationRestrictions=[])))

    def test_formato_de_paises_como_objetos(self):
        v = vacante(locationRestrictions=[{"alpha2": "CO", "name": "Colombia", "slug": "colombia"}])
        self.assertIsNone(self.motivo(v))

    def test_no_acepta_colombia(self):
        self.assertIn("No acepta", self.motivo(vacante(locationRestrictions=["Brazil"])))

    def test_expirada(self):
        self.assertEqual(self.motivo(vacante(expiryDate=1000)), "Vacante expirada")

    def test_fecha_en_milisegundos_tambien_funciona(self):
        self.assertIsNone(self.motivo(vacante(expiryDate=FUTURO * 1000)))
        self.assertEqual(self.motivo(vacante(expiryDate=1000 * 1000)), "Vacante expirada")

    def test_tiempo_parcial(self):
        self.assertIn("Tipo de contrato", self.motivo(vacante(employmentType="Part Time")))

    def test_part_time_en_el_titulo(self):
        self.assertIn("medio tiempo", self.motivo(vacante(title="Accountant - Part time")))

    def test_titulo_senior(self):
        self.assertIn("nivel alto", self.motivo(vacante(title="Senior Financial Analyst")))

    def test_vp_no_coincide_dentro_de_otra_palabra(self):
        self.assertIsNone(self.motivo(vacante(title="Financial Analyst (VPN tools)")))

    def test_fuera_de_perfil(self):
        self.assertIn("Fuera del perfil", self.motivo(vacante(title="Python Cloud Engineer")))

    def test_idioma_que_no_hablo(self):
        self.assertIn("idioma", self.motivo(vacante(title="Dutch AI Data Rater")))

    def test_ingles_no_descarta(self):
        self.assertIsNone(self.motivo(vacante(title="Data Analyst (English fluency)")))

    def test_seniority_solo_alta(self):
        self.assertIn("Nivel demasiado alto", self.motivo(vacante(title="Analyst", seniority=["Director"])))

    def test_experiencia_alta(self):
        v = vacante(description="<p>Requirements: 5+ years of experience in FP&A.</p>" + RELLENO)
        self.assertEqual(self.motivo(v), "Pide 5+ años de experiencia")

    def test_experiencia_en_rango(self):
        v = vacante(description="<p>2-3 years of relevant experience.</p>" + RELLENO)
        self.assertIsNone(self.motivo(v))

    def test_experiencia_en_espanol(self):
        v = vacante(description="<p>Mínimo 4 años de experiencia como analista.</p>" + RELLENO)
        self.assertEqual(self.motivo(v), "Pide 4+ años de experiencia")

    def test_experiencia_minima_en_espanol(self):
        # Caso real (Consultec-TI): "experiencia mínima de 3 años en ..." se colaba.
        v = vacante(description="<p>Requisitos: experiencia mínima de 3 años en análisis de procesos.</p>" + RELLENO)
        self.assertEqual(self.motivo(v), "Pide 3+ años de experiencia")

    def test_titulo_con_letras_decoradas(self):
        # Caso real: títulos con letras matemáticas en negrita esquivaban las reglas de título.
        self.assertIn("nivel alto", self.motivo(vacante(title="𝗦𝗲𝗻𝗶𝗼𝗿 𝗔𝗻𝗮𝗹𝘆𝘀𝘁")))

    def test_repetida_de_la_misma_empresa_deja_una(self):
        # Caso real (Adaptive Teams): el mismo aviso dos veces. Debe quedar una, no cero.
        a = vacante(guid="a", companyName="Misma Empresa")
        b = vacante(guid="b", companyName="Misma Empresa")
        pasan, descartadas = filtros.evaluar([a, b], CONFIG)
        self.assertEqual([v["guid"] for v, _ in pasan], ["a"])
        self.assertEqual([v["guid"] for v, _ in descartadas], ["b"])
        self.assertIn("Repetida", descartadas[0][1])

    def test_certificacion_obligatoria(self):
        v = vacante(description="<p>CPA certification is required.</p>" + RELLENO)
        self.assertEqual(self.motivo(v), "Exige certificación CPA")

    def test_certificacion_deseable_no_descarta(self):
        v = vacante(description="<p>A CFA is a plus.</p>" + RELLENO)
        self.assertIsNone(self.motivo(v))

    def test_contradiccion_ubicacion(self):
        v = vacante(locationRestrictions=[],
                    description="<p>You must be authorized to work in the United States.</p>" + RELLENO)
        self.assertIn("Contradicción", self.motivo(v))

    def test_comision(self):
        v = vacante(description="<p>This is a commission-based role with great upside.</p>" + RELLENO)
        self.assertIn("comisión", self.motivo(v))

    def test_copy_of(self):
        self.assertIn("Copy of", self.motivo(vacante(title="Copy of Finance Analyst")))

    def test_zona_horaria_incompatible(self):
        v = vacante(timezoneRestrictions=["UTC+8", "UTC+9"])
        self.assertIn("Zona horaria", self.motivo(v))

    def test_zona_horaria_compatible(self):
        self.assertIsNone(self.motivo(vacante(timezoneRestrictions=["UTC-5", "UTC-4"])))

    def test_plantilla_repetida_en_dos_empresas(self):
        a = vacante(guid="a", companyName="Empresa A")
        b = vacante(guid="b", companyName="Empresa B")
        c = vacante(guid="c", companyName="Empresa C", description="<p>Texto distinto y único.</p>" + RELLENO + " x")
        pasan, descartadas = filtros.evaluar([a, b, c], CONFIG)
        self.assertEqual({v["guid"] for v, _ in descartadas}, {"a", "b"})
        self.assertEqual([v["guid"] for v, _ in pasan], ["c"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
