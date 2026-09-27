# TODO

Remise à niveau du fork `j5lien/enocean`. Cocher au fur et à mesure. Les étapes numérotées sont à faire dans l'ordre :
d'abord assainir, ensuite retravailler l'API publique, puis la documenter.

## 1. Bugs et nettoyage (avant de retoucher l'API publique)

Bugs :

- [ ] `Packet(type, bytearray(...))` perd silencieusement ses données (`data` remplacé par `[]`) : accepter
      `bytes`/`bytearray`
- [ ] Décodage VLD multi-commandes sans `command=` : c'est la première variante du profil qui s'applique, pas celle de
      la trame (ex. D2-01-12 : une commande 1 d'un contrôleur est décodée avec la structure de la commande 4). Détecter
      la commande depuis le champ `<command>` du profil
- [ ] `UTETeachInPacket.number_of_channels` n'est jamais lu (toujours `0xFF`) ; la valeur est dans `channel`
- [ ] `RadioPacket.learn` vaut toujours `True` pour les VLD (pas de bit d'apprentissage) : `None` ou documenter
- [ ] `packet.received` : `datetime` naïf, et seulement renseigné par le communicator (le sniffer le formate avec `%z`,
      qui sort vide) : horodatage UTC avec fuseau
- [ ] `SerialCommunicator` n'accepte pas `teach_in` (le sniffer le modifie après `start()`, avec une course possible)
      et son port par défaut est `/dev/ttyAMA0` (UART de Raspberry Pi)
- [ ] Setter de `base_id` documenté « only for testing purposes » alors qu'il a des usages réels
- [ ] A5-04-02 : plage brute de la température à 0..255 au lieu de 0..250 (à confirmer avec la spec EEP)
- [ ] `TCPCommunicator` est en réception seule (`send()` sans effet, réponses teach-in non transmises) et ne sert
      qu'un client à la fois : à revoir si un usage bidirectionnel est souhaité

Dépréciations à retirer (changements incompatibles : version 2.0, avec guide de migration) :

- [ ] Alias `PACKET.RADIO` / `PACKET.RADIO_ADVANCED` : ce sont les noms canoniques de l'enum (`PACKET(1).name` vaut
      `RADIO`), faire de `RADIO_ERP1` / `RADIO_ERP2` les noms canoniques puis retirer les alias
- [ ] Paramètre `bitarray` de `EEP.find_profile()`, jamais utilisé
- [ ] `enocean.decorators` (outil de test livré dans le package) et les tests `@timing`, inactifs sans
      `WITH_TIMINGS=1` : supprimer, ou passer à `pytest-benchmark` si les performances doivent être suivies
- [ ] `script-files` (déprécié par setuptools) qui installe `enocean_example.py` dans le PATH : supprimer, ou le
      remplacer par un point d'entrée `[project.scripts]`
- [ ] Ré-export de `RORG` dans `enocean.protocol.eep` (« left as a helper »)

## 2. API d'intégration (d'après l'usage dans enocean-sniffer)

- [ ] Registre d'appareils : identifiant → EEP (et nom, pièce, métadonnées libres), décodage automatique à la
      réception (`packet.parsed` rempli), profil par défaut par RORG pour les appareils inconnus, liste d'exclusion.
      Remplace les tables `KNOWN_DEVICES` / `NOT_MY_DEVICES` / `EXCLUDED_DEVICES` et les `select_eep()` du sniffer
- [ ] `packet.to_dict()` sérialisable en JSON : identifiants en hexadécimal, noms de RORG et de type de paquet (sans
      lever d'exception pour une valeur inconnue : `RORG(x)` plante aujourd'hui), champs décodés, dBm, horodatage ISO.
      Le sniffer construit ce dictionnaire à la main et lit l'attribut privé `_bit_status`
- [ ] Émission haut niveau vers les actionneurs : D2-01 (sortie d'un canal ou de tous avec `IO=0x1E`), D2-05 (aller à
      une position, stop, demander la position), avec le base ID (ou base ID + décalage) comme émetteur
- [ ] Teach-in : appairer la clé à un actionneur (requête et réponse UTE), au lieu de forger les octets à la main
- [ ] API publique déclarée : exports dans `enocean/__init__.py` (`from enocean import SerialCommunicator,
      RadioPacket, RORG`), `__all__`, nommage cohérent (`dBm` / `dbm`)
- [ ] Introspection des profils : lister les champs d'un profil et leurs valeurs possibles depuis le code (aujourd'hui
      uniquement dans `SUPPORTED_PROFILES.md`)
- [ ] Refaire enocean-sniffer avec la nouvelle version : valide l'API sur un vrai projet (registre, `to_dict()`,
      métriques Prometheus et logs JSON)

## 3. Documentation de l'API

- [ ] Docstrings sur toute l'API publique (54 classes/fonctions publiques sur 89 n'en ont pas) : paramètres, retour,
      exceptions, exemple sur les points d'entrée ; règles ruff `D` en CI pour ne plus en oublier
- [ ] Site de documentation (mkdocs + mkdocstrings, GitHub Pages) : concepts (ESP3, EEP, RORG/FUNC/TYPE, base ID,
      teach-in), recettes (recevoir, décoder, envoyer, superviser, Docker avec `/dev/serial/by-id`), référence d'API
      générée ; exemples exécutés en CI
- [ ] Guide de migration 0.60 → 1.x → 2.0 (utile pour enocean-sniffer)

## Tests

- [ ] Compléter `test_real_frames.py` avec d'autres appareils : volets D2-05-00, compteur EWattch A5-12-01,
      détecteur de fumée D2-14-30
- [ ] Test matériel optionnel avec émission radio (après teach-in de la clé sur un actionneur de test)

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
