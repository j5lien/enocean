# TODO

Remise à niveau du fork `j5lien/enocean`. Cocher au fur et à mesure.

## En cours

- [ ] Ouvrir la PR `e2e-communicator-tests` → `main` et vérifier la CI (macOS runner, skip Windows des tests série)

## Tests

- [ ] Trames réelles capturées sur tes appareils (D2-01-12, D2-14-30, D2-14-41, …) avec les valeurs affichées par
      l'appareil, pour valider le décodage contre la réalité (les tests actuels vérifient la cohérence d'`EEP.xml`
      et figent le décodage, pas sa conformité à la spec)
- [ ] Décider du sort des tests `@timing` (inactifs sans `WITH_TIMINGS=1`) : les supprimer ou passer à `pytest-benchmark`
- [ ] Couvrir `consolelogger.py` (0 %) ou le supprimer s'il ne sert qu'aux exemples

## Bugs

- [ ] `Communicator.base_id` : bloque jusqu'à 1 s, et vide puis remplit à nouveau la queue `receive`
      (réordonne les paquets reçus pendant l'attente)
- [ ] `SerialCommunicator` : une `SerialException` à l'écriture arrête le thread sans rien logger
- [ ] `TCPCommunicator` : ignore la queue d'envoi (`send()` sans effet), n'accepte ni `callback` ni `teach_in`,
      ne parse qu'à la déconnexion du client ou après 0,5 s d'inactivité

## Montées de version / modernisation

- [ ] Remonter la version minimale de `pyserial` (`>=3.0`, 2015)
- [ ] `ruff format` sur tout le code (commit dédié), puis règles ruff supplémentaires (`UP`, `B`, `I`, `SIM`)
- [ ] Annotations de type + `mypy` en CI + `py.typed`
- [ ] Remplacer `script-files` (déprécié) par un point d'entrée `[project.scripts]`, vérifier que les exemples
      fonctionnent encore
- [ ] Hooks `pre-commit` (ruff, lock uv)

## Documentation / métadonnées

- [ ] Réécrire le README : installation (`sudo pip`, `python-pip` obsolètes), installation depuis le fork,
      environnement de dev (`make install`, `make test`)
- [ ] Métadonnées du package : URL (pointe vers `kipe/enocean`), mainteneur, numéro de version, CHANGELOG

## Dépôt GitHub

- [ ] Détacher le fork de `kipe/enocean` pour que les PR visent `j5lien/enocean` par défaut
- [ ] `gh auth login -h github.com` pour pouvoir créer les PR et suivre la CI depuis le terminal
- [ ] Activer les alertes Dependabot et CodeQL (Settings → Code security)
- [ ] Protéger `main` : CI obligatoire avant merge
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
