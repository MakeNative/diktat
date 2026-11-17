# Diktat

Sprechen statt tippen: Du sprichst im Browser, Diktat schreibt mit und legt den Text in die
Zwischenablage. Mit ⌘V fügst du ihn ein, wo du willst, etwa in eine Mail, einen Chat oder Claude.

Alles läuft auf deinem Mac. Deine Aufnahmen gehen an keinen Server und an keinen
Dienst. Nur das Sprachmodell ([Whisper](https://github.com/openai/whisper) von OpenAI) wird
beim ersten Start einmal heruntergeladen.

## Was du brauchst

- einen Mac mit Apple-Chip (M1 oder neuer)
- etwa 3 GB freien Speicher
- Internet für die Installation und den ersten Start

## Installieren

1. Öffne das Programm **Terminal**: ⌘ + Leertaste drücken, „Terminal“ tippen, Enter.
2. Kopiere diese Zeile, füge sie ins Terminal ein und drücke Enter:

   ```
   curl -LsSf https://raw.githubusercontent.com/MakeNative/diktat/main/install.sh | sh
   ```

3. Warte, bis „Fertig“ erscheint. Das dauert ein paar Minuten. Danach kannst du das Terminal schließen.

Diktat öffnet sich danach von selbst im Browser.

## Benutzen

1. **Diktat öffnen:** ⌘ + Leertaste, „Diktat“ tippen, Enter. Diktat öffnet sich im Browser.
2. **Beim ersten Mal:** Diktat lädt das Sprachmodell herunter (etwa 1,6 GB). Den Fortschritt
   siehst du auf der Seite. Danach fragt der Browser, ob die Seite das Mikrofon benutzen darf:
   **Erlauben**.
3. **Sprechen:**
   - **Leertaste gedrückt halten** und sprechen. Beim Loslassen schreibt Diktat mit.
   - Oder die **Leertaste kurz tippen**, sprechen und zum Beenden noch einmal tippen.
   - Oder auf den roten Knopf klicken.
4. **Einfügen:** Der Text liegt schon in der Zwischenablage. Mit ⌘V fügst du ihn ein.

Die letzten 30 Texte stehen unter **Verlauf**. Ein Klick auf einen Eintrag kopiert ihn wieder.
Oben rechts stellst du die Sprache ein: Deutsch, Englisch oder Automatisch.

Diktat beendet sich nach einer Stunde ohne Nutzung von selbst. Willst du es früher beenden,
klick unten auf **Diktat beenden**. Zum Weitermachen öffnest du einfach wieder die App.

## Aktualisieren

Führe die Zeile aus [Installieren](#installieren) noch einmal aus.

## Probleme

| Was passiert | Was hilft |
|---|---|
| „Kein Mikrofonzugriff“ | In den Browser-Einstellungen das Mikrofon für `127.0.0.1` erlauben. Außerdem unter Systemeinstellungen → Datenschutz & Sicherheit → Mikrofon dem Browser den Zugriff erlauben. |
| „Diktat läuft nicht mehr“ | Die App „Diktat“ wieder öffnen. |
| „Port 8765 ist belegt“ | Ein anderes Programm nutzt den Port. Im Terminal `DIKTAT_PORT=8766 diktat` starten. |
| Der Text kommt nicht in die Zwischenablage | Auf **Kopieren** klicken. Manche Browser erlauben das automatische Kopieren nicht. |
| Fachbegriffe oder Namen werden falsch geschrieben | Das liegt am Sprachmodell. Den Text vor dem Absenden kurz durchsehen. |

Was Diktat im Hintergrund tut, steht in `~/Library/Logs/Diktat.log`.

## Deinstallieren

```
uv tool uninstall diktat
rm -rf ~/Applications/Diktat.app ~/.cache/whisper
```

## Für Entwickler

`diktat` startet den Server im Terminal und öffnet die Seite. `diktat --detach` startet ihn
im Hintergrund, so ruft die App ihn auf. Einstellungen über Umgebungsvariablen:

| Variable | Standard | Bedeutung |
|---|---|---|
| `DIKTAT_MODEL` | `large-v3-turbo` | Whisper-Modell, z. B. `small` für schwächere Macs |
| `DIKTAT_PORT` | `8765` | Port des lokalen Servers |
| `DIKTAT_IDLE_MINUTES` | `60` | Minuten ohne Nutzung bis zum Beenden |

Der Server lauscht nur auf `127.0.0.1` und nimmt nur Anfragen der eigenen Seite an. Andere
Webseiten im selben Browser können ihm also nichts schicken. Das Audio wandelt der Browser selbst
in 16 kHz mono um, deshalb braucht Diktat kein ffmpeg.

Lokal entwickeln:

```
uv run diktat
```

## MakeNative

Dieses Werkzeug ist Teil von [MakeNative](https://makenative.de). Wir arbeiten jeden Tag mit
Agenten-Pipelines und bringen anderen bei, sie für ihre eigenen Prozesse zu
bauen. Für Entwickler genauso wie für alle, die ihre Arbeit mit KI automatisieren wollen.

Du willst das für deine Arbeit lernen? Trag dich in die Liste ein:
[Bewerbung Starter-Kohorte](https://tally.so/r/5ByYj6?utm_source=github&utm_medium=readme&utm_campaign=starter-kohorte)

Christian Eichmüller · [LinkedIn](https://linkedin.com/in/christianeichmueller)

## Lizenz

MIT
