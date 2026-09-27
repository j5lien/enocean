# TODO

Remise à niveau du fork `j5lien/enocean`. Cocher au fur et à mesure.

## Tests

- [ ] Compléter `test_real_frames.py` avec d'autres appareils : volets D2-05-00, compteur EWattch A5-12-01,
      détecteur de fumée D2-14-30 ; vérifier A5-04-02 (plage de température 0..255 au lieu de 0..250 dans la spec ?)
- [ ] Test matériel optionnel avec émission radio (après teach-in de la clé sur un actionneur de test)
- [ ] Décider du sort des tests `@timing` (inactifs sans `WITH_TIMINGS=1`) : les supprimer ou passer à `pytest-benchmark`

## Bugs

- [ ] `TCPCommunicator` est en réception seule (`send()` sans effet, réponses teach-in non transmises) et ne sert
      qu'un client à la fois ; à revoir si un usage bidirectionnel est souhaité

## Montées de version / modernisation

- [ ] Remplacer `script-files` (déprécié) par un point d'entrée `[project.scripts]`, vérifier que les exemples
      fonctionnent encore

## Documentation / métadonnées


## Opérabilité

- [ ] Exemple de dashboard Grafana et de règles d'alerte Prometheus (module injoignable, silence radio, hausse des
      erreurs CRC, échecs du base ID)

## Dépôt GitHub

- [ ] `gh auth login -h github.com` pour pouvoir créer les PR et suivre la CI depuis le terminal
- [ ] Activer les alertes Dependabot et CodeQL (Settings → Code security)
- [ ] Publication PyPI : pas pour l'instant (le nom `enocean` appartient au projet d'origine)

## Fait

- [x] Environnement de dev : `uv`, `pyproject.toml`, `Makefile`, `pytest` (nose ne marche plus sur Python ≥ 3.10), `ruff`
- [x] CI GitHub Actions (lint, tests 3.10–3.14 Linux + macOS/Windows, build + smoke test du wheel) et Dependabot
- [x] Branche de référence `main`, anciennes branches supprimées
- [x] Tests de bout en bout des communicators (pty pour le série, sockets pour le TCP), `make test-linux`
- [x] Transport TCP réparé (crash à chaque connexion, `send_to_tcp_socket` cassé en Python 3)
- [x] Tests de robustesse du parseur (`hypothesis`) ; resynchronisation ESP3 corrigée (CRC d'en-tête vérifié avant
      d'attendre la longueur annoncée, seul le `0x55` est sauté en cas d'erreur) ; trames radio sans données
      optionnelles acceptées ; trames trop courtes renvoyées brutes au lieu de lever une exception
- [x] Tests sur tous les profils EEP (structure, aller-retour create/parse, snapshot du décodage) ; corrections
      dans `EEP.xml` (D2-01-12 : enums en binaire, plages trop larges ; D2-14-30/41 : `bits` manquant) ; décodage
      des télégrammes tronqués ; `SUPPORTED_PROFILES.md` régénéré et vérifié en CI ; seuil de couverture 90 %
- [x] `EEP.xml` chargé avec `xml.etree` (bibliothèque standard) au lieu de BeautifulSoup/`html.parser` : dépendance
      supprimée, décodage identique (snapshot), chargement 20× plus rapide, plus aucun warning
- [x] Restes de Python 2 supprimés (dont la dépendance `enum-compat`), `ruff format` appliqué, règles ruff
      `I`/`UP`/`B`/`SIM`, lint étendu aux exemples et au générateur
- [x] `base_id` : plus de vidage/réordonnancement de la queue, fonctionne en mode callback ; teach-in UTE reçu avant
      que le base ID soit connu : le base ID est demandé puis la réponse envoyée (avant : blocage 1 s du thread,
      `TypeError`, paquet perdu) ; `TCPCommunicator` accepte `callback`/`teach_in` et livre les paquets au fil de
      l'eau ; erreur d'écriture série loggée
- [x] README réécrit (installation depuis le fork, exemples vérifiés, développement), métadonnées du package
      (URL du fork, mainteneur, mots-clés), `consolelogger.py` testé (couverture de la librairie : 97 %)
- [x] Package entièrement typé (`mypy --strict` en CI, `py.typed`, `FieldValue` pour `packet.parsed`) ;
      `.git-blame-ignore-revs` pour le commit de formatage
- [x] Hooks pre-commit (`make hooks`) utilisant les outils de `uv.lock` ; `pyserial>=3.5`
- [x] Release 1.0.0 : `CHANGELOG.md`, workflow de release sur tag (release GitHub avec wheel/sdist, sans PyPI)
- [x] Fork détaché de `kipe/enocean`, `main` protégée
- [x] Logs : niveaux revus (bruit radio en DEBUG, télégramme corrompu en WARNING, traces complètes des erreurs de
      callback), `NullHandler`, champs structurés (`packet_type`, `rorg`, `sender`, `dbm`), `init_logging(json_format=True)`
- [x] Statistiques internes (`communicator.stats`) et santé (`communicator.health()`), sans dépendance
- [x] Adaptateur Prometheus optionnel (`enocean[prometheus]`, `enocean.prometheus.register()`) : namespace, labels
      constants, registry et plusieurs communicators configurables
- [x] Métriques par émetteur (paquets, dernier vu, dBm) en option et bornées (`per_sender=True`, `max_senders`)
- [x] Tests matériels sur une vraie clé (`make test-hardware`, config `.env`, test interactif interrupteur → lumière)
      et trames réelles en tests CI (PTM 210 F6-02-02, SIN-2-2-01 D2-01-12)
