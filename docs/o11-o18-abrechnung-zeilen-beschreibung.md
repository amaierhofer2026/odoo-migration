# Rechnungszeilen - Spalte "Beschreibung" (Odoo 11 gegen Odoo 18)

Stand: 05.10.2026, Session 125. Bereich Abrechnung bleibt IN ARBEIT; finale Abnahme durch Anna.
Odoo 11 wurde ausschliesslich lesend geprueft (JSON-RPC, `scripts/_o11_zeilen_spalten.py`,
`scripts/_o11_zeilen_formular.py`, `scripts/_o11_zeilen_vererbung.py`).

## 1. Fehlerbild (von Anna im Browser gefunden)

Im Rechnungsformular, Reiter "Rechnungszeilen":

- die Spalte "Beschreibung" fehlte in der Tabelle vollstaendig,
- im Spaltenauswahl-Menue stand "Beschreibung" zweimal.

Reproduziert und belegt mit `scripts/_sonde_zeilen_dom.py` (lokale Instanz):

```
Kopfzeilen der Zeilentabelle: Pos | Produkt | Sektion | Kostenstelle | Menge | Preis pro ME |
                              Rabatt (%) | Steuern | Zwischensumme | Total      <- ohne Beschreibung
Spaltenauswahl: Pos, Produkt, Sektion, Beschreibung, Beschreibung, Kostenstelle, Menge,
                Maßeinheit, Rabatt (%), Steuern, Total                         <- zweimal
Beschreibungstext im DOM der Tabelle: nicht vorhanden
```

## 2. Ursache

**Zwei getrennte Ursachen, die zusammenwirken.**

**a) Der doppelte Eintrag im Spaltenauswahl-Menue** stammt aus der eigenen Ansicht
`views/account_move_line_columns.xml`. Dort war ein zweiter `name`-Knoten direkt hinter den
vorhandenen gesetzt worden:

```xml
<xpath expr="//field[@name='invoice_line_ids']//field[@name='name']" position="after">
    <field name="name" id="itk_o11_beschreibung" string="Beschreibung" optional="show"/>
</xpath>
```

Damit steht `name` zweimal in der Arch. Beide Knoten haben `optional="show"` und tragen die
Beschriftung "Beschreibung" - das Menue listet beide.

**b) Die fehlende Spalte** kommt von Odoo 18 selbst. Die Zeilenliste traegt das Widget
`product_label_section_and_note_field_o2m`
(`account/static/src/components/product_label_section_and_note_field/product_label_section_and_note_field.js`).
Dessen Renderer entfernt die Spalte `name` bewusst aus der gerenderten Tabelle:

```js
getActiveColumns(list) {
    const productCol = activeColumns.find((col) => this.productColumns.includes(col.name));
    const labelCol = activeColumns.find((col) => col.name === "name");
    if (productCol) {
        ...
        activeColumns = activeColumns.filter((col) => col.name !== "name");
```

Der Beschreibungstext wird stattdessen in die Produktzelle gezeichnet ("Produkt + Beschreibung in
einer Spalte"). Da unsere Ansicht `product_id` zusaetzlich auf das einfache Widget `many2one`
umstellt, zeigte die Produktzelle den Text ebenfalls nicht - die Beschreibung war damit **gar nicht
sichtbar**, obwohl sie in der Datenbank steht.

Die Arch zur Laufzeit (vor der Korrektur, `scripts/pruefe_zeilenspalten.py`):

```
  1 invoice_line_ids  widget=product_label_section_and_note_field_o2m
  2 sequence          string=Pos widget=handle
  3 number            string=Pos optional=show
  4 product_id        string=Produkt optional=show widget=many2one
  5 display_type      string=Sektion optional=show
  6 name              string=Beschreibung optional=show widget=text
  7 name              string=Beschreibung optional=show id=itk_o11_beschreibung   <- Doppelung
  8 analytic_distribution ...
```

## 3. Richtige Zuordnung (Odoo 11 -> Odoo 18)

| Odoo 11 | Odoo 18 | Regel |
|---|---|---|
| `account.invoice.line.name` (Spalte "Beschreibung") | `account.move.line.name` | 1:1, gleiches Feld, keine Umbenennung |

Andere Felder tragen in Odoo 18 zwar Beschriftungen wie "Beschreibung" im Umfeld, das fachliche
Feld der Zeilenbeschreibung ist aber eindeutig `account.move.line.name`. Es war nie das falsche
Feld - falsch war die doppelte Einblendung und das Zeilen-Widget.

## 4. Odoo-11-Position (read-only gemessen)

`account.invoice.form` (View 594) + Vererbungen 1044 (`layout_category_id` = Sektion) und
1270 (`number` = Line No.):

```
sequence(handle) | number | product_id | layout_category_id(Sektion) | name(Beschreibung) |
account_id(Konto) | account_analytic_id(Kostenstelle) | analytic_tag_ids | quantity |
uom_id | price_unit | discount | invoice_line_tax_ids | price_subtotal
```

"Beschreibung" steht also **direkt nach der Sektion, vor Kostenstelle** - genau dort, wo sie jetzt in
Odoo 18 wieder erscheint.

## 5. Korrektur (Modul `itk_account_migration` 18.0.1.12.0)

In `views/account_move_line_columns.xml`:

1. Der zusaetzlich eingefuegte zweite `name`-Knoten ist **entfernt** (Ursache des doppelten
   Menue-Eintrags).
2. Die Zeilenliste nutzt jetzt das Odoo-18-Standardwidget `section_and_note_one2many` statt
   `product_label_section_and_note_field_o2m`. Dessen Renderer laesst die Spalte `name` stehen.
3. Auf `name` bleiben nur `string="Beschreibung"` und `optional="show"`; das von Odoo 18 gesetzte
   Widget `section_and_note_text` wird **nicht** mehr ueberschrieben (die fruehere Ueberschreibung
   auf `text` ist entfernt).

Technische Feldnamen, Modelle und Datenlogik sind unveraendert; es wurde keine einzige Zeile Python
angefasst.

### Was sich sichtbar aendert

- Vorher: keine Spalte "Beschreibung", dafuer zwei Menue-Eintraege "Beschreibung".
- Nachher: genau eine Spalte "Beschreibung" in Odoo-11-Position, mit dem echten Wert, editierbar;
  Menue-Eintrag genau einmal.

### Bewusste Folge (bitte mitentscheiden, Anna)

Odoo 18 zeichnet Produkt und Beschreibung in **einer** Zelle (Produktspalte, mit
Beschreibungs-Zeile und einem kleinen Zusatz-Knopf). Diese Darstellung ist mit einer eigenen
Odoo-11-Spalte "Beschreibung" technisch nicht kombinierbar: der Renderer entfernt die Spalte
`name`, sobald er aktiv ist. Mit `section_and_note_one2many` entfaellt daher die
Beschreibungs-Zeile in der Produktzelle; der Text steht dafuer vollstaendig in der eigenen Spalte
und ist dort direkt bearbeitbar. Alle uebrigen Odoo-18-Funktionen der Zeilenliste bleiben
(Abschnitte fett, Notizen kursiv, Zeilen verschieben, Zeile/Abschnitt/Notiz hinzufuegen, Katalog,
sichtbare Spaltenauswahl, optionale Spalten).

## 6. Browser-Abnahme (`scripts/browser_zeilen_beschreibung.py`)

Geprueft fuer alle vier Belegarten (Ausgangsrechnung, Kunden-Gutschrift, Eingangsrechnung,
Lieferanten-Gutschrift) - sie nutzen alle dieselbe Ansicht `account.view_move_form`:

| Pruefung | Ergebnis |
|---|---|
| Spalte "Beschreibung" genau einmal sichtbar | ja, Position 5 (direkt nach "Sektion") |
| Beschreibungstext aus der Datenbank sichtbar | "BESCHREIBUNG <Belegart>" in der Produktzeile |
| Spaltenauswahl-Menue | "Beschreibung" genau einmal, keine doppelten Eintraege |
| andere Spalten | Pos, Produkt, Sektion, Kostenstelle, Menge, Preis pro ME, Rabatt (%), Steuern, Zwischensumme, Total - je genau einmal |
| Abschnitts- und Notizzeile | vorhanden, Abschnitt als Abschnitt gezeichnet |
| Griffspalte, Zeile/Abschnitt/Notiz hinzufuegen, Katalog | vorhanden |
| Eingabe | Zelle wird zum Eingabefeld, Wert aenderbar, nichts gespeichert (DB-Wert unveraendert) |

Werkzeuge: `scripts/pruefe_zeilenspalten.py` (Arch der Zeilenliste je Belegart),
`scripts/_zeilen_testdaten.py` (Testbelege je Belegart anlegen/pruefen/aufraeumen),
`scripts/browser_zeilen_beschreibung.py` (Browserabnahme).

## 7. Ergebnis lokal und VM

| Pruefung | lokal | VM |
|---|---|---|
| Spalte "Beschreibung" genau einmal, Position nach "Sektion" | ja (alle vier Belegarten) | ja (alle vier Belegarten) |
| Beschreibungstext sichtbar | ja | ja |
| Spaltenauswahl ohne Doppelung | ja | ja |
| Abschnitt/Notiz, Griffspalte, Zeile/Abschnitt/Notiz/Katalog | vorhanden | vorhanden |
| Eingabe moeglich, nichts gespeichert | ja | ja |
| Browserlauf `browser_zeilen_beschreibung.py` | 112 OK / 0 FEHL | 112 OK / 0 FEHL |
| Screenshots | `Desktop/Odoo18-Abnahme-Session125/zeilen_beschreibung/lokal` | `.../vm` |

Weitere Nachweise derselben Runde: Modulversion 18.0.1.12.0 lokal = VM, Feldbeschriftungen
155 Feldpaare / 0 Abweichungen (lokal und VM), View-Bezeichnungen ohne unbegruendete Abweichung,
Feldabdeckung 273 belegte Felder / 0 Luecken, Regression Verkauf/Abonnements 886 OK / 0 FEHL,
Modul- und Menuevergleich lokal = VM ohne Abweichung.

Testdaten restlos entfernt: lokal 40 -> 44 -> 40 Belege (106 -> 122 -> 106 Zeilen),
VM 62 -> 66 -> 62 Belege (170 -> 186 -> 170 Zeilen).

**Betriebslehre:** In Odoo 18 ist `installed_version` kein Datenbankfeld mehr, sondern ein
berechnetes Feld aus dem Manifest auf der Platte - der laufende Server haelt den beim Start
gelesenen Wert fest. Nach einem Upgrade ueber einen zweiten Prozess zeigt der laufende Server
deshalb weiter die alte Version, obwohl die Datei neu ist; erst ein Neustart
(`docker restart odoo18` bzw. `docker compose restart odoo`) gleicht die Anzeige an.

