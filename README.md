# Pflegedienst Malaika GmbH – Website (Entwicklung)

Statischer, responsiver HTML-first-Auftritt in der Farbpalette Burgundy & Blush. Aktuelle Konfiguration: **nicht indexieren** (Meta-Robots noindex auf allen Seiten), ohne Analytics/Tracking-Skripte, ohne Formular oder Cookies im eigenen Seitencode.

## Struktur
- Startseite; Leistungen ausschließlich mit bestätigter Grundpflege und Behandlungspflege
- Pflege für Angehörige, Pflegeberatung, Einzugsgebiet, Über uns, Kontakt
- Ratgeber einschließlich allgemeiner Informationen über Hauswirtschaftliche Hilfe und Verhinderungspflege, Impressum und vorläufige Datenschutzhinweise

## Vor öffentlicher Suchfreigabe zu erledigen
1. Rechtsprüfung von Impressum und vollständiger Datenschutzerklärung, Einbau der finalen Hosting-Informationen.
2. Leistungsumfang, Team, Einzugsgebiet, Kapazitäten, Kontaktinformationen und Bürozeiten mit der Geschäftsführung bestätigen.
3. Domain/Hosting/Canonical URL prüfen. Die derzeitige Canonical-URL verweist auf den erwarteten GitHub-Pages-Projektpfad.
4. Erst danach noindex entfernen, Sitemap generieren, Google/Bing Search Console aktivieren, Crawler-/Mobil-/Link-Tests durchführen.
5. Daten im Impressum: Handelsregisterauszug vom 02.11.2026 (HRB 289768 B); Telefon und Bürozeiten aus der vorhandenen Malaika-Broschüre. Andere Dienstleistungsbroschüren sind keine Belege für Malaikas Leistungsumfang.

Keine Gesundheitsdaten, internen Unterlagen, Schlüssel oder Zugänge in diesem öffentlichen Repository speichern.

## Hinweis zu GitHub Pages und Indexierung
Alle HTML-Seiten enthalten `noindex`. Eine Datei `robots.txt` im Projekt-Unterpfad ersetzt nicht die `robots.txt` der Host-Wurzel `pflegehelfergmbh.github.io`. Die HTML-Meta-Anweisung ist für die temporäre Nichtindexierung entscheidend. GitHub Pages muss separat in den Repository-Einstellungen aktiviert und der öffentlich abrufbare Stand nach erfolgreicher Bereitstellung überprüft werden.



## Navigationsregel
Interne Links öffnen im selben Tab. Nur externe HTTP(S)-Links zu fremden Domains öffnen mit `target="_blank" rel="noopener"` in einem neuen Tab. Telefon- und E-Mail-Links bleiben im selben Kontext.

## Dauerhafter Navigationsstandard (ab 02.11.2026)
- Alle Links innerhalb der Website (einschließlich **Home**, Logo, Navigation und Footer) bleiben im aktuellen Tab: `target="_self"` oder kein target.
- Nur externe HTTP(S)-Links zu anderen Domains öffnen im neuen Tab: `target="_blank" rel="noopener"`.
- E-Mail-, Telefon- und interne Sprungmarken bleiben ohne neue Tabs.
- `scripts/check_navigation.py` wird beim Push automatisch per GitHub Actions geprüft und schützt alle HTML-Seiten vor dieser Regression; `noindex` bleibt bis zur Freigabe der Website bestehen.

## Redaktionelle Strukturentscheidung vom 02.11.2026
- Keine identischen FAQ-Blöcke auf unterschiedlichen Seiten. Fragen und Antworten passen jeweils zu Suchintention und Seitenthema.
- Kontakt-CTA dürfen überall vorkommen; Überschrift und Einstieg werden individuell formuliert.
- Eigene Leistungen: **Grundpflege** und **Behandlungspflege**. Allgemeine Informationen zu Hauswirtschaft und Verhinderungspflege stehen im **Ratgeber**, bis der Leistungsumfang bestätigt ist. Alte URLs unter /leistungen/ bleiben als kurze Umzugsseiten erreichbar; sie sind nicht mehr in der Leistungsübersicht verlinkt.
- Keine internen Produktionshinweise, Recherchehinweise oder künstlichen Vertrauensbehauptungen im Kunden-Fließtext. Rechtlich nötige transparente Hinweise und Entwurfsstatus bleiben sichtbar.
- Kundenseitig bestätigte Merkmale: ambulante Pflege, mobile Mitarbeitende, Einsatzgebiete in sieben benannten Berliner Zonen, Sprachen Deutsch/Russisch/Englisch/Französisch.
- Verbindliche Kostenübernahme der Pflege- oder Krankenkasse wird nie pauschal zugesagt.
