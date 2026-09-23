# Uebergabe Session 119 - Bereich Abonnements (Stand 22.09.2026)

Diese Datei ist die Arbeitsgrundlage fuer die naechste Session. Kurzfassung: der Bereich
**Abonnements ist fachlich abgeschlossen** (Teile 1-14), auf der VM im echten Browser abgenommen
und in der Checkliste als *vollstaendig funktionsfaehig und vollstaendig migrationsvorbereitet*
markiert. Offen ist nur der Merge des letzten PRs und danach der Abgleich lokal/GitHub/VM.

## 1. Was in dieser Session (119) gemacht wurde

```
Teil 14 "Abonnement Produkte" fertiggestellt und abgenommen:
   - Listenansicht: categ_id "Interne Kategorie", is_multi_factor_product "Mit Faktor
     multiplizieren (pro 1.000)" - beide sichtbar und in der Spaltenauswahl
   - neue Suchansicht product.template.search.abo.produkte: Filter "Mit Faktor multipliziert"
     und "Aktive Abonnement Produkte", Gruppierungen "Status" (product_type_id) und
     "Mit Faktor multipliziert"; Odoo-18-Filter/-Gruppierungen erhalten
   - to_multiply_by_factor aus dem Produktformular entfernt (Feld bleibt in der DB, Daten
     unveraendert)
   - Lager geprueft: stock wird NICHT installiert, Bestandsmenge/Geplante Bestandsmenge
     entfallen begruendet
   - Gesamtbereich Abonnements erneut gegengeprueft (alle Werkzeuge gruen)
Bereichsdokument: docs/o11-o18-vergleich-abo-teil14.md
```

## 2. Entscheidungen (durch Anna freigegeben)

```
1. to_multiply_by_factor: JA, aus dem Produktformular entfernen. Belegt: das Feld existiert in
   Odoo 11 gar nicht (nur is_multi_factor_product, dort 1 Produkt true). Reine Migrationsdublette,
   0 Verwendungen im Code. qty_multiplication_factor auf den Zeilen ist unberuehrt.
2. stock: NICHT installieren. Odoo 11 hatte stock installiert, aber nie genutzt - read-only
   belegt: 0 erledigte Lagerbewegungen (327 moves: 288 assigned/39 storniert), 252 Lieferauftraege
   ohne einen einzigen erledigten, 0 stock.quant, 0 Bestellvorschlaege, 1 Standard-Lagerhaus
   (WH "My Company"), 13 Standard-Lagerorte, 0 von 649 Produkten mit Bestand != 0, 0 Lagerartikel,
   82 Produkte mit negativer "Geplanter Bestandsmenge" (= nur die offenen Ausgaenge).
3. Odoo-11-Filter "Service Type ..." NICHT nachbauen - sie hatten Einzelwerte der ITK-Produktart
   fest verdrahtet; Odoo 18 leistet das ueber die Gruppierung "Status" (product_type_id).
```

## 3. Stand der Repos und Instanzen

```
main (GitHub)          = ec2c896 (PR #92 und #93 gemergt)
PR #94                 OFFEN, mergeable=clean - Branch hermes/session-119-abo-produkte-doku
                         369cffd docs(session-119) Teil 14 + Checkliste + PROJECT_KNOWLEDGE
                                + Korrektur der Uebergabe Session 118
                         e2aa6c0 fix(scripts) drei Pruefwerkzeuge korrigiert
                         (diese Uebergabe-Datei kommt als weiterer Commit hinzu)
lokal                  Arbeitsbaum auf dem Branch hermes/session-119-abo-produkte-doku, sauber
VM /opt/odoo18         = ec2c896 (per git pull --ff-only), Container laeuft, /web/login HTTP 200
Module lokal und VM    itk_subscription 18.0.1.2.1 | itk_product 18.0.1.0.1 |
                       itk_multifactor 18.0.1.1.1 - alle Upgrades fehlerfrei
Odoo 11 Prod           unveraendert, ausschliesslich read-only gelesen
```

## 4. Nachweise (alle Zahlen aus dieser Session)

```
lokal:  verify_abo_produkte 34 OK/0 FEHL | browser_abo_produkte 47 OK/0 FEHL
VM:     verify_abo_produkte 34 OK/0 FEHL | browser_abo_produkte 47 OK/0 FEHL
        verify_s118_abo 19 OK/0 FEHL | pruefe_abo_xmlids 0 fehlende XML-IDs
        test_abo_rechnungslauf 13 OK/0 FEHL | test_abo_manuelle_rechnung 16 OK/0 FEHL
        test_abo_smartbuttons 11 OK/0 FEHL | browser_abo_abschluss 55 OK/0 FEHL
        Screenshots: Desktop\Odoo18-Abnahme-Session119\60..66_VM_*.png
```

## 5. Naechste Schritte (in dieser Reihenfolge)

```
1. Merge PR #94 (Merge-Commit, kein Squash/Rebase) - Anna gibt frei bzw. merged selbst.
2. Lokal: git checkout main && git pull --ff-only; VM: cd /opt/odoo18 && git pull --ff-only.
   Doku-/Werkzeug-Aenderungen brauchen KEINEN Container-Neustart und KEIN Modul-Upgrade.
3. Danach ist der Bereich Abonnements abgeschlossen. Offen bleiben nur die bekannten
   DATENSCHRITTE der Migration (nicht Teil der Code-Bereitschaft):
      - Auswahlregel der 42 Alt-Abos ohne Verkaufsauftrag (Odoo 11: Altbestand 2013/2014)
      - Reihenfolge: Auftraege vor Abos
      - 8 bestaetigte USD-Testauftraege (nur Testdaten, von Migration/Abnahme ausgeschlossen)
      - Uebernahme der NV-Nummern, Rechnungsstellung nach der Migration
      - recurring_next_date 1:1 uebernehmen, Cronjobs vor der Migration pausieren
   Regeln dazu: migration/abo_migrationsregeln.json
4. Naechster Bereich ausserhalb der Abos: siehe MIGRATION_READINESS_CHECKLIST.md
   (Abschnitt 6). Vorher keine Bereichsmarkierung ohne Browserabnahme auf der VM.
```

## 6. Arbeitsregeln (unveraendert gueltig)

```
- Odoo 11 Prod NUR lesend. Nichts aendern/anlegen/loeschen. Keine Datenmigration ohne Freigabe.
- Abnahme nur auf der VM (k001959vsx.ipax.at) im ECHTEN Browser mit echten Klicks; Sichtbarkeit
  im DOM genuegt nicht. Kein Button gilt ohne Klick auf der VM als funktionsfaehig.
- Lokal ist Entwicklung, VM ist Abnahmeumgebung; beide getrennt ausweisen.
- Kein Force-Push, kein Rebase, kein Auto-Merge, nichts direkt auf main: Arbeitsbranch + PR.
- Vor jedem Modul-Upgrade: XML gegen Odoo-RNG pruefen und die Ansicht als Testdatensatz
  anlegen/rendern/loeschen (scripts/pruefe_view_render.py).
- Windows/Docker: Aenderungen am __manifest__.py sieht der laufende Container nicht -
  erst docker restart odoo18, dann upgrade_modules.py --update-list (sonst "alte Version ->
  alte Version").
- VM-Zugang: SSH Port 22 war in dieser Session offen (Helfer:
  %LOCALAPPDATA%\Temp\vm_exec.py "befehl"). Ist er zu, fuehrt Anna EINEN Befehl pro Turn aus.
```

## 7. Werkzeuge fuer diesen Bereich (scripts/)

```
vergleich_abo_produkte.py --instanz o11|vm|lokal   Bestandsaufnahme O11 gegen O18
analyse_o11_lager.py, analyse_o11_lager_teil2.py   Lager-Nutzung Odoo 11 (read-only)
dump_o18_ansichten.py --art list|search|form       zusammengefuehrter Odoo-18-Arch (roh)
pruefe_view_render.py --datei <view.xml>           Ansicht als Testdatensatz rendern
verify_abo_produkte.py --instanz lokal|vm          Umsetzung Abonnement Produkte (34 Pruefungen)
browser_abo_produkte.py --instanz lokal|vm         Browserabnahme mit echten Klicks (47 Pruefungen)
verify_s118_abo.py, pruefe_abo_xmlids.py, test_abo_rechnungslauf.py,
test_abo_manuelle_rechnung.py, test_abo_smartbuttons.py, browser_abo_abschluss.py
```

## 8. Befunde dieser Session (Details in PROJECT_KNOWLEDGE.md, Session 119)

```
F35  Faktor-Feld war im Produktformular unsichtbar: Anker //field[@name='list_price'] trifft in
     Odoo 18 das Feld INNERHALB von <div name="list_price_uom"/>. Behoben (Anker auf das div).
F36  pruefe_abo_xmlids.py zaehlte 12 Phantom-Fehler: Muster ref="..." traf auch href="...".
     Werkzeug korrigiert, jetzt 0 fehlende XML-IDs.
F37  test_abo_smartbuttons.py waehlte "keine Rechnung" per Suche auf das NICHT gespeicherte
     Berechnungsfeld invoice_count (falscher Treffer) -> Auswahl jetzt ueber read().
F38  Versionsangaben 18.0.1.2.3 bis 18.0.1.2.6 in den Session-118-Dokumenten sind nicht belegt;
     Repo und DB stehen auf itk_subscription 18.0.1.2.1 (1.0.0 -> 1.1.0 -> 1.2.0 -> 1.2.1).
F39  Sicherheitsfund: das Klartext-Kennwort der Odoo-11-Prod-Instanz stand in
     scripts/browser_abo_pruef.py. Entfernt, jetzt aus der gitignorierten .env.
F40  browser_abo_abschluss.py prueft den Ziel-Smart-Button ueber das URL-Muster; Odoo 18 nutzt
     sprechende URLs (/odoo/sale.subscription/172/invoicing). Werkzeug korrigiert (Brotkrumen).
```

## 9. Dokumentierte Abweichungen (bewusst, nicht umbenannt)

```
default_code         im Formular "Referenz" (Odoo 18 Basismodul), in der Liste wie Odoo 11
                     "Interne Referenz"
product_type_id      im Formular "Produkttyp" (Odoo 11: "Product-Type"), in der Liste "Status"
Spalte "Produktart"  Odoo 18 blendet Listenspalten nicht mehr ueber invisible="1" aus (dafuer
                     column_invisible); die Spalte bleibt als Odoo-18-Zusatzspalte sichtbar
```
