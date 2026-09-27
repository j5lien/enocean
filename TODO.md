# TODO

Remise à niveau du fork `j5lien/enocean`. Cocher au fur et à mesure.

## En cours

- [ ] Ouvrir la PR `e2e-communicator-tests` → `main` et vérifier la CI (macOS runner, skip Windows des tests série)

## Tests

- [ ] Une trame de référence par profil EEP (29/65 profils testés aujourd'hui), en commençant par les D2
      ajoutés en 2022 (D2-01-12, D2-14-30, …) — table de trames + valeurs attendues, tests paramétrés
- [ ] Tests aller-retour `RadioPacket.create()` → `parse_msg()` → `parse_eep()` pour chaque profil supporté
- [ ] Tests de robustesse du parseur avec `hypothesis` : ne plante jamais, ne boucle jamais, se resynchronise
- [ ] Seuil de couverture minimum en CI (`--cov-fail-under`)
- [ ] Décider du sort des tests `@timing` (inactifs sans `WITH_TIMINGS=1`) : les supprimer ou passer à `pytest-benchmark`
- [ ] Couvrir `consolelogger.py` (0 %) ou le supprimer s'il ne sert qu'aux exemples

## Bugs

- [ ] Resynchronisation ESP3 : sur CRC d'en-tête invalide, le parseur fait confiance à la longueur annoncée et jette
      les trames valides qui suivent. Il faut sauter uniquement le `0x55` et chercher le suivant (spec ESP3)
- [ ] Revoir les `except Exception` larges ajoutés dans `Packet.parse_msg` : une erreur de construction de paquet
      est remontée comme `CRC_MISMATCH`
- [ ] `Communicator.base_id` : bloque jusqu'à 1 s, et vide puis remplit à nouveau la queue `receive`
      (réordonne les paquets reçus pendant l'attente)
- [ ] `SerialCommunicator` : une `SerialException` à l'écriture arrête le thread sans rien logger
- [ ] `TCPCommunicator` : ignore la queue d'envoi (`send()` sans effet), n'accepte ni `callback` ni `teach_in`,
      ne parse qu'à la déconnexion du client ou après 0,5 s d'inactivité

## Montées de version / modernisation

- [ ] Parser `EEP.xml` avec un vrai parseur XML (`lxml` ou `xml.etree`) au lieu de `html.parser`
      (`XMLParsedAsHTMLWarning`) — vérifier que le décodage reste identique sur tous les profils
- [ ] `logger.warn` → `logger.warning`
- [ ] Supprimer les restes de Python 2 : `from __future__`, fallback `Queue`, `ord()` dans `parse_msg`,
      `super(Class, self)`, dépendance `enum-compat`
- [ ] Remonter les versions minimales des dépendances (`beautifulsoup4>=4.3.2`, `pyserial>=3.0`)
- [ ] `ruff format` sur tout le code (commit dédié), puis règles ruff supplémentaires (`UP`, `B`, `I`, `SIM`)
- [ ] Annotations de type + `mypy` en CI + `py.typed`
- [ ] Remplacer `script-files` (déprécié) par un point d'entrée `[project.scripts]`, vérifier que les exemples
      fonctionnent encore
- [ ] Vérifier en CI que `SUPPORTED_PROFILES.md` est à jour par rapport à `EEP.xml`
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
