"""ITK Website: Laufzeit-Setup.

Die sichtbaren Menue-Bezeichnungen der Website-Verwaltung sind Moduldaten mit
`noupdate=0` - ein Upgrade des Moduls `website` setzt sie zurueck, waehrend die
alte Uebersetzung in der Datenbank stehen bleibt. Deshalb wird das Setup bei
jeder Installation und bei jedem Upgrade erneut ausgefuehrt (idempotent).
"""
import logging

_logger = logging.getLogger(__name__)

# Sichtbare Bezeichnungen der Website-Verwaltung (Entscheidung E13, Session 142).
# Quelle: Odoo 18 zeigt "Website > Site"; Odoo 11 nannte den Bereich "Webseite".
# "Analytics" ist im deutschen Backend englisch - hier "Analysen".
_MENUE_NAMEN = {
    "website.menu_site": "Webseite",
    "website.menu_website_analytics": "Analysen",
}


def _benenne_menue(env, xmlid, name):
    menu = env.ref(xmlid, raise_if_not_found=False)
    if not menu:
        return False
    # Quelle UND beide Sprachen schreiben (Muster aus itk_crm, Session 114):
    # ein Upgrade des Quellmoduls setzt die Quelle zurueck, die de_DE-Uebersetzung
    # bleibt aber stehen - nur so ist die Anzeige nach jedem Upgrade korrekt.
    menu.write({"name": name})
    menu.with_context(lang="de_DE").write({"name": name})
    menu.with_context(lang="en_US").write({"name": name})
    return True


def setup_all(env):
    """Idempotent: Menue-Bezeichnungen der Website-Verwaltung setzen und den
    Odoo-Demo-Kontaktblock im Kopf (Telefon/Mail) deaktivieren."""
    geaendert = []
    for xmlid, name in _MENUE_NAMEN.items():
        if _benenne_menue(env, xmlid, name):
            geaendert.append("%s=%s" % (xmlid, name))

    # Odoo 18 rendert im Kopf einen Muster-Kontaktblock (Telefon +1 555-555-5556,
    # info@yourcompany.example.com). Odoo 11 hatte so einen Block nicht und es
    # duerfen keine erfundenen Kontaktdaten stehen bleiben -> Ansicht deaktivieren.
    kontakt = env.ref("website.header_text_element", raise_if_not_found=False)
    if kontakt and kontakt.active:
        kontakt.active = False
        geaendert.append("website.header_text_element=inaktiv")

    _logger.info("itk_website Setup: %s", ", ".join(geaendert) or "keine Aenderung")
    return geaendert
