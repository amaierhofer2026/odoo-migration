"""Gezieltes Nachladen einzelner PO-Eintraege aus dem Repo (Odoo-Shell-Skript).

Hintergrund: `ir.module.module._load_module_terms()` wird bei einem Modul-Upgrade mit
overwrite=False aufgerufen. Fuer einfache Uebersetzungsfelder (translate=True) gilt dann
`t.value || m.feld` - ein bereits vorhandener (falscher) de_DE-Wert in der DB gewinnt und
der korrekte .po-Wert wird NICHT gesetzt. Dieses Skript laedt genau die betroffenen
Eintraege mit overwrite=True nach - ohne Nebenwirkungen, weil per xmlids-Filter nur die
angegebenen Datensaetze angefasst werden.

Aufruf (lokal):
  docker exec -i -e TERMS_MODULES=itk_base_setup \
      -e TERMS_XMLIDS=account_edi_ubl_cii.field_res_partner__peppol_endpoint \
      odoo18 sh -c 'odoo shell -d odoo18_test --no-http --db_host=db --db_user=odoo \
                    --db_password="$PASSWORD"' < scripts/load_terms_de.py

Aufruf (VM):
  docker compose exec -T odoo env TERMS_MODULES=... TERMS_XMLIDS=... \
      odoo shell -d odoo18_test --no-http < /opt/odoo18/scripts/load_terms_de.py

Nur lesende Kontrolle: TERMS_OVERWRITE=0 setzen (dann wird nichts geschrieben).
"""
import os

from odoo.tools.translate import TranslationImporter

MODULE = [m for m in os.environ.get("TERMS_MODULES", "").split(",") if m]
XMLIDS = {x for x in os.environ.get("TERMS_XMLIDS", "").split(",") if x}
LANG = os.environ.get("TERMS_LANG", "de_DE")
OVERWRITE = os.environ.get("TERMS_OVERWRITE", "1") == "1"
ADDONS = os.environ.get("TERMS_ADDONS", "/mnt/extra-addons")


def zeige(titel):
    print("%s" % titel)
    for xmlid in sorted(XMLIDS):
        modul, name = xmlid.split(".", 1)
        daten = env["ir.model.data"].search(
            [("module", "=", modul), ("name", "=", name)], limit=1)
        if not daten:
            print("   %-62s NICHT GEFUNDEN" % xmlid)
            continue
        env.cr.execute(
            'SELECT x."%s" FROM "%s" x WHERE x.id = %%s'
            % ("field_description" if daten.model == "ir.model.fields" else "arch_db",
               "ir_model_fields" if daten.model == "ir.model.fields" else "ir_ui_view"),
            (daten.res_id,))
        roh = env.cr.fetchone()
        wert = roh[0] if roh else None
        if isinstance(wert, dict):
            print("   %-62s %s" % (xmlid, wert.get(LANG, wert.get("en_US"))))
        elif isinstance(wert, str):
            print("   %-62s %s" % (xmlid, "de_DE vorhanden" if '"de_DE"' in wert else "kein de_DE"))
        else:
            print("   %-62s %r" % (xmlid, wert))


print("Module: %s | Sprache: %s | overwrite=%s | xmlids=%d"
      % (", ".join(MODULE), LANG, OVERWRITE, len(XMLIDS)))
zeige("VORHER:")
if OVERWRITE:
    importer = TranslationImporter(env.cr, verbose=False)
    kurz = LANG.split("_")[0]
    for modul in MODULE:
        pfad = "%s/%s/i18n/%s.po" % (ADDONS, modul, kurz)
        importer.load_file(pfad, LANG, xmlids=XMLIDS or None)
        print("   geladen: %s" % pfad)
    importer.save(overwrite=True, force_overwrite=True)
    env.cr.commit()
    env.invalidate_all()
    print("   gespeichert (overwrite=True)")
    zeige("NACHHER:")
else:
    print("(TERMS_OVERWRITE=0 - nur Kontrolle, nichts geschrieben)")
