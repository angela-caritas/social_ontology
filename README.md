# Social Ontology / CariGraph

**Deutschsprachiger Begriffs- und Wissensgraph für die Sozialberatung.** Das Repository enthält kuratierte Fachvokabulare, Zuordnungen zwischen verschiedenen Kategoriensystemen sowie Python-Werkzeuge. Ursprünglich wurde es entwickelt, um daraus einen JSON-basierten Wissensgraphen und Importdaten für das Wissensmanagementtool "CariFIX" innerhalb des Deutschen Caritasverbandes e.V. zu erzeugen.

> **Projektstatus:** Forschungs-/Prototypenstand (`ontology/v1`). Dies ist ein eigenes JSON-Graphmodell, keine unmittelbar bereitgestellte OWL-, RDF- oder SKOS-Datei. Das Projekt, in dem es erstellt wurde, hatte seine aktive Phase von 11/20 - 12/22. Die enthaltenen Informationen wurden seitdem nicht aktualisiert. Allerdings handelt es sich um generelle Konzepte des Sozialwesens, die nicht so schnell veralten. 

## Was kann man damit machen?
Für diese Aufgaben wurde die Ontologie entwickelt - darüber hinaus gibt es viele weitere Ideen, wofür die Ontologie als eigenes Ergebnis ausgekoppelt wirksam sein könnte:
- **Fachbegriffe zusammenführen:** Kategorien aus Fachanwendungen wie Crea Client, Vivendi und EBIS sowie Fachvokabulare und Glossare sind hier in einem gemeinsamen Graphen verbunden und können erweitert werden.
- **Verwandte Begriffe finden:** Hierarchische, assoziative und synonymähnliche Beziehungen können erkundet werden.
- **Fachtexte grob verschlagworten:** Ein regelbasierter Extraktor ordnet Texten Begriffe über Zeichenkettenvergleiche zu. Damit können Texte kategorisiert werden.
- **Daten für Anwendungen vorbereiten:** Vorhandene JSON-Dateien liefern Konzepte, alternative Bezeichnungen, Dokumente und gewichtete Dokument-Konzept-Zuordnungen.
- **Datenqualität und Interoperabilität erforschen:** Mapping-Qualität untersuchen und die Graphdaten für eigene Such- oder Wissensanwendungen aufbereiten.

Das Repository enthält **keine fertige Weboberfläche, API, Datenbank oder produktionsreife KI-Beratung**.

## Aufbau

```text
ontology/v1/
├── data/
│   ├── raw/                    # Ausgangskategorien und Mapping-Tabellen
│   └── processed/              # Aufbereitete Glossare und CariFIX-Seed-Daten
├── preprocessing/
│   └── ontology_loader.py      # Graphaufbau (CariGraph)
├── extractor/
│   └── extractor.py            # Konzept-Extraktion und CariFIX-Konzept-Export
├── enricher/
│   └── document_enricher.py    # Dokument-Konzept-Zuordnung
└── main.py                     # Platzhalter (leer)
logos/                           # Projektgrafiken
README.md
```

### Inhalt und Quellen

Der Graph wird aus folgenden Teilbeständen zusammengestellt: Schemata aus den Fachanwendungen zur Dokumentation (Crea Client, Vivendi für Migrationsberatung, EBIS für Migrationsberatung), Caritas.de - Glossar, Asyl.net, Glossar zu Schuldnerberatung (ursprünglich veröffentlicht unter geldundschulden.de) sowie einem Thesaurus mit alternativen Begriffen. Weitere aufbereitete Dateien enthalten das Raphaelswerk-Glossar und händisch kuratierte CariFIX-Dokumentdaten.

**Beispielhafte Bestandsaufnahme (lokaler Neuaufbau mit den Dateien dieses Repositories):** 3.682 Knoten und 5.473 Kanten; 717 Basiskonzepte (Dimensionen, Themen und Root-Labels), 2.123 alternative Label-Knoten. Die mitgelieferten CariFIX-Seed-Dateien enthalten 717 Konzepte, 3.289 alternative Labels sowie 2.623 Dokumente mit 4.897 Dokument-Konzept-Zuordnungen. Das sind Bestandszahlen, keine Qualitätskennzahlen.

## Voraussetzungen

- Python mit Unterstützung für die im Quellcode verwendeten Typannotationen (`str | None`, `list[str]`), beispielsweise Python 3.10 oder neuer.
- Für die vorhandenen Skripte werden ausschließlich Module der Python-Standardbibliothek verwendet.

## Graph erzeugen

Vom Repository-Hauptverzeichnis aus:

```bash
PYTHONPATH=. python ontology/v1/preprocessing/ontology_loader.py
```

Ergebnis: `ontology/v1/data/processed/carigraph_v1.json`. Diese Datei wird im Repository mit Stand 11/26 mitgeliefert, kann aber auch durch das Skript neu erzeugt werden.

Der JSON-Graph besitzt die Schlüssel `nodes` und `edges`. Knoten tragen u. a. `label`, `uri`, `uuid`, `concept_source`, `concept_type`, `description`, `url` und `parent_label_uuid`. Kanten enthalten `source`, `target`, `directed` und `hierachical` (Schreibweise im vorhandenen Code).

### Begriffe aus Text extrahieren

Nach der Graphgenerierung:

```python
from ontology.v1.extractor.extractor import CaritasExtractor

extractor = CaritasExtractor(
    "ontology/v1/data/processed/carigraph_v1.json"
)
print(extractor.extract_concepts("Ich benötige eine Arbeitserlaubnis und habe Schulden."))
```

Der Extraktor arbeitet mit einer aus dem Graphen generierten Menge alternativer Bezeichnungen und sucht diese ohne Groß-/Kleinschreibungsunterscheidung im Text. Das ist **keine semantische KI-Analyse**: Wortgrenzen, Mehrdeutigkeiten und Negationen werden nicht zuverlässig behandelt.

### CariFIX-Konzepte neu exportieren

```bash
PYTHONPATH=. python ontology/v1/extractor/extractor.py
```

Ergebnis: `ontology/v1/data/processed/carifix_seed_concepts_v1.json`. Bei erneuter Erzeugung werden UUIDs für alternative Labels neu vergeben; diese sind deshalb nicht dauerhaft stabil.

### Dokumente anreichern

`document_enricher.py` enthält Funktionen zur Aufbereitung von Glossar- und Artikeldaten. Sein derzeitiger `__main__`-Einstieg setzt allerdings Eingabedateien voraus, die **nicht im Repository vorhanden** sind (`data/raw/glossary.json`, `data/raw/raphaelswerk_glossary.json` und `data/raw/neue_caritas_articles.json`). Der entsprechende Befehl funktioniert daher mit dem Repository allein nicht unverändert. Die bereits erzeugte Datei `carifix_seed_documents_v1.json` ist nutzbar.

## Bekannte Einschränkungen

- Der Graph enthält beim aktuellen Neuaufbau mehrfache `uri`-Werte und Kanten, deren Endpunkte nicht existieren; vor einem produktiven Einsatz sollten diese validiert und bereinigt werden.
- Einige Beziehungen sind grobe Zuordnungen; das Feld `hierachical` bezeichnet nicht in allen Fällen eine ontologisch strenge Ober-/Unterbegriffsrelation.
- Knoten-UUIDs werden beim Graphaufbau zufällig erzeugt. IDs aus mehreren Erzeugungsläufen sollten nicht ohne Abgleich vermischt werden.
- Es gibt bislang keine dokumentierte Versionsstrategie, keine automatisierten Tests und keine mitgelieferte Standardontologie in OWL/RDF/SKOS.

## Hintergrund

Die Arbeit entstand im Umfeld des Caritas-Projekts **„Lernende Systeme in der Beratung“** (2020–2022). Dabei wurde unter anderem der Prototyp **CariFIX** entwickelt. Das vorliegende Repository enthält hierfür verwendete beziehungsweise vorbereitete Wissens- und Importdaten sowie den Code zum Graphaufbau; es ist nicht die vollständige CariFIX-Anwendung.
Das Projekt wurde 2020-2022 vom Bundesministerium für Familie, Senioren, Frauen und Jugend (BMFSFJ) im Rahmen der KI-Strategie des Bundes/KI-Zukunftsfonds und der Agenda für Smarte Gesellschaftspolitik gefördert.

Weitere Informationen zum abgeschlossenen Projekt: https://www.caritas-digital.de/projekte/lernende-systeme-in-der-beratung/

<img src="./logos/Caritas-Logo.jpg" width="130"> <img src="./logos/BMFSFJ gefördert vom.jpg" width="250"> <img src="./logos/Logo_bunt-e1662710104640.jpg" width="300">

Kontakt: digitale-transformation@caritas.de
