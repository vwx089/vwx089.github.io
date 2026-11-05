# Stefans Apps für SideStore

Gemeinsame SideStore-Quelle für alle meine Apps. In SideStore › Sources › + einmalig eintragen:

```
https://vwx089.github.io/source.json
```

## So funktioniert es

`.github/workflows/source.yml` liest alle 15 Minuten die Releases der Repos aus `apps.json`,
baut daraus mit `build_source.py` die `source.json` und speichert sie hier. GitHub Pages liefert sie aus.
Die App-Repos selbst brauchen dafür nichts Besonderes, sie müssen nur ihre `.ipa` als Release veröffentlichen.

## Neue App hinzufügen

Einen Eintrag in `apps.json` ergänzen: `repo`, `asset` (Name der `.ipa` im Release), `bundleIdentifier`,
Name, Texte, Icon-URL. Die App-Repo muss **öffentlich** sein, sonst kann SideStore die `.ipa` nicht laden.

Mit kostenloser Apple-ID zählen SideStore und jede installierte App zum Limit von 3 Apps.
