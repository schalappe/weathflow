# Conseil financier personnel

Ce contexte fixe le vocabulaire utilisé pour produire un conseil financier personnel à partir des transactions et des faits fournis par l’utilisateur.

## Language

**Données observées**:
Faits financiers calculés directement depuis les transactions importées et leurs tendances.
_Avoid_: Données utilisateur, contexte connu

**Contexte déclaré**:
Faits financiers fournis ou confirmés par l’utilisateur et qui ne peuvent pas être déduits sûrement des transactions.
_Avoid_: Données observées, profil utilisateur

**Fait matériel**:
Fait dont une variation plausible peut changer la bonne action, sa priorité, son montant ou son échéance, ou justifier une conclusion sans action.
_Avoid_: Information utile, détail personnel

**Recommandation personnalisée**:
Recommandation dont le contenu décisionnel réagit aux faits matériels de l’utilisateur, plutôt que de seulement reformuler un conseil générique avec ses chiffres.
_Avoid_: Conseil contextualisé, conseil chiffré

**Préférence soutenable**:
Choix déclaré compatible avec les obligations, la trésorerie et les objectifs financiers connus.
_Avoid_: Préférence utilisateur

**Conclusion sans action**:
Conclusion explicite qu’aucune action financière n’est justifiée par les faits disponibles.
_Avoid_: Absence de réponse, conseil vide

**Défaut invalidant**:
Défaut d’une recommandation qui rend la réponse entière impropre à être présentée comme personnalisée.
_Avoid_: Imperfection, réserve

**Clarification utile**:
Question dont la réponse peut départager des sorties décisionnelles différentes et que l’utilisateur peut raisonnablement fournir.
_Avoid_: Question utile, collecte de contexte

**Recommandation robuste à l’incertitude**:
Recommandation qui reste valide pour toutes les valeurs plausibles d’un fait matériel incertain.
_Avoid_: Conseil prudent, conseil par défaut

**Réponse sélective**:
Réponse qui ne présente que les recommandations robustes et rend explicites les sujets sur lesquels aucune conclusion n’est étayée.
_Avoid_: Réponse partielle, conseil incomplet

**Réponse de session**:
Fait fourni pour le conseil en cours que l’utilisateur choisit de ne pas réutiliser.
_Avoid_: Fait temporaire, contexte mémorisé

**Fait mémorisé**:
Fait du contexte déclaré conservé pour de futurs conseils avec l’accord annoncé de l’utilisateur.
_Avoid_: Profil utilisateur, souvenir

**Fait durable**:
Fait mémorisé sans échéance prévisible, actif jusqu’à sa correction ou sa suppression.
_Avoid_: Fait permanent

**Fait daté**:
Fait mémorisé dont la validité se termine à une date connue.
_Avoid_: Fait temporaire

**Fait volatil**:
Fait mémorisé susceptible de changer, valide pendant une fenêtre de fraîcheur propre à sa nature.
_Avoid_: Fait daté, donnée observée

**Fait expiré**:
Fait mémorisé dont la validité a pris fin, visible mais exclu du conseil jusqu’à sa reconfirmation.
_Avoid_: Fait supprimé, fait actif

**Fait à confirmer**:
Fait mémorisé expiré ou rendu incertain par une contradiction matérielle, qui reste visible mais ne peut plus influencer un conseil jusqu’à sa confirmation ou sa correction.
_Avoid_: Fait actif, fait supprimé

**Trace de décision**:
Explication structurée qui relie une sortie à ses faits décisionnels, leur provenance, la règle ou le calcul appliqué, les conventions contestables, l’effet de l’incertitude et les conditions qui changeraient la sortie.
_Avoid_: Raisonnement interne, justification libre

**État d’incertitude décisionnel**:
Qualification d’une sortie par l’effet observable de l’incertitude restante : étayée, robuste malgré une limite explicite, ou sujet non conclu.
_Avoid_: Score de confiance, probabilité subjective
