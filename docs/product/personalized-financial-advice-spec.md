# Spécification produit — Conseil financier personnel

**Version normative : 1.0**  
**Statut : validé pour planification**  
**Carte de provenance :** [Définir un conseil financier réellement personnalisé](https://github.com/schalappe/weathflow/issues/34)

Ce document est autonome et normatif. Les liens vers les décisions d’origine servent uniquement à établir leur provenance.

## 1. Destination, périmètre et hors périmètre

### 1.1 Destination

Le parcours produit un conseil personnel qui ne questionne l’utilisateur que lorsqu’une incertitude financière peut changer la bonne sortie. Il fournit ensuite des recommandations explicables sur le budget, les dettes, le fonds d’urgence, les objectifs et la trajectoire d’épargne.

La présente spécification fixe les comportements observables nécessaires pour planifier ce parcours sans prescrire son architecture ni son implémentation.

### 1.2 Périmètre

Le parcours :

- utilise l’historique des transactions et les tendances comme **données observées** ;
- utilise uniquement les faits financiers explicitement fournis ou confirmés comme **contexte déclaré** ;
- distingue toujours ces deux provenances ;
- évalue la matérialité des incertitudes avant de poser une question ;
- produit une recommandation, une conclusion sans action ou un sujet non conclu ;
- autorise l’utilisateur à passer, corriger et supprimer les faits déclarés ;
- rend chaque sortie contestable par une trace de décision reliée à ses sources ;
- est destiné à un usage personnel unique.

Les domaines de conseil autorisés sont le budget, les dettes, le fonds d’urgence, les objectifs financiers et la trajectoire d’épargne.

### 1.3 Hors périmètre

Sont exclus :

- l’architecture, le modèle de données, les API, la migration, l’implémentation, le choix de modèle LLM et le découpage du backlog ;
- le produit multi-utilisateur et le parcours conseiller-client ;
- le contexte de vie général sans conséquence financière explicitement structurée ;
- le coaching conversationnel continu et le suivi d’engagements ;
- les recommandations de placements ou de produits financiers, la fiscalité et la gestion patrimoniale ;
- l’invention d’intentions, de causes comportementales, d’usages ou de récurrences à partir des seuls flux.

## 2. Vocabulaire et invariants produit

### 2.1 Vocabulaire

| Terme | Définition normative |
|---|---|
| **Données observées** | Faits financiers calculés directement depuis les transactions importées et leurs tendances. |
| **Contexte déclaré** | Faits financiers fournis ou confirmés par l’utilisateur et qui ne peuvent pas être déduits sûrement des transactions. |
| **Fait matériel** | Fait dont une variation plausible peut changer l’action, sa priorité, son montant, son échéance ou l’abstention. |
| **Recommandation personnalisée** | Recommandation dont le contenu décisionnel réagit aux faits matériels, et non simple reformulation d’un conseil générique avec les chiffres de l’utilisateur. |
| **Préférence soutenable** | Choix déclaré compatible avec les obligations, la trésorerie et les objectifs financiers connus. |
| **Conclusion sans action** | Conclusion explicite qu’aucune action financière n’est justifiée par les faits disponibles. |
| **Clarification utile** | Question dont la réponse peut départager des sorties décisionnelles différentes et que l’utilisateur peut raisonnablement fournir. |
| **Recommandation robuste à l’incertitude** | Recommandation valide pour toutes les valeurs plausibles d’un fait matériel incertain. |
| **Réponse sélective** | Réponse qui conserve les recommandations robustes et marque explicitement les autres sujets comme non conclus. |
| **Réponse de session** | Fait fourni pour le conseil courant, sans réutilisation ultérieure. |
| **Fait mémorisé** | Fait déclaré conservé pour de futurs conseils après annonce visible et sans choix « Cette fois seulement ». |
| **Fait durable** | Fait mémorisé sans expiration temporelle, actif jusqu’à correction ou suppression. |
| **Fait daté** | Fait mémorisé dont la validité se termine à une date connue. |
| **Fait volatil** | Fait mémorisé dont la validité se termine après une fenêtre de fraîcheur définie. |
| **Fait à confirmer** | Fait expiré ou contesté, visible mais incapable d’influencer un conseil avant confirmation ou correction. |
| **Trace de décision** | Explication structurée reliant une sortie à ses faits décisionnels, leur provenance, ses règles ou calculs, ses conventions contestables et l’effet de l’incertitude. |
| **État d’incertitude décisionnel** | Qualification observable d’une sortie : étayée, robuste malgré une limite explicite, ou sujet non conclu. |
| **Fait à portée étroite** | Fait valable uniquement pour la transaction, la série, la période, le poste ou l’action explicitement qualifiés. |
| **Réserve liquide non affectée** | Montant immédiatement disponible, non engagé par une obligation connue et non réservé à un objectif. |
| **Plancher de sécurité** | Réserve minimale que l’utilisateur choisit de protéger tant que ses obligations restent couvertes. |
| **Priorité active** | Unique objectif personnel orientant actuellement la trajectoire d’épargne, sans supplanter les obligations. |

### 2.2 Invariants

1. Une recommandation est l’unité de contrôle ; une seule recommandation invalide rend la réponse entière invalide.
2. Un fait matériel absent, incertain, contradictoire, incomplet ou périmé ne devient jamais implicitement vrai.
3. Les obligations et contraintes dures priment ; une préférence soutenable reste respectée.
4. Le repère 50/30/20 ne prévaut jamais sur un objectif ou une répartition soutenable explicitement choisis.
5. Un montant, une économie ou une échéance n’est présenté que s’il est dérivable des faits disponibles.
6. Le parcours peut conclure qu’aucune action n’est justifiée ; il ne remplit aucun quota de recommandations.
7. Une donnée observée ne remplace, ne corrige, ne clôt ni ne supprime seule un fait déclaré.
8. Une clarification porte sur un seul fait décisionnel, reste passable et consomme au maximum trois questions par demande de conseil.
9. Une correction ou suppression retire immédiatement toute sortie qui dépendait du fait précédent, ou la recalcule avant nouvel affichage valide.
10. Toute sortie est reliée à une trace de décision ; aucun raisonnement interne brut ni score de confiance arbitraire n’est présenté.

## 3. Contrats produit observables

### C-01 — Provenance et matérialité

**Entrées métier :** données observées avec période et périmètre ; faits déclarés avec valeur, portée, état et dernière confirmation ; demande de conseil.

1. Le parcours identifie pour chaque sortie les faits qui peuvent changer son action, sa priorité, son montant, son échéance ou son abstention.
2. Chaque fait décisionnel est étiqueté **observé** ou **déclaré** ; les deux provenances ne sont jamais fusionnées.
3. La complétude d’une période ou d’un périmètre n’est tenue pour vraie que si elle est établie. Une absence observée n’est probante que sur un périmètre déclaré complet et sans trou.
4. Une intention, un usage, une cause comportementale, une récurrence ou le suivi d’un ancien conseil ne sont jamais inférés sans confirmation pertinente.
5. Pour chaque recommandation, un scénario contrefactuel modifiant un seul fait matériel doit modifier la sortie décisionnelle lorsque la bonne décision devrait changer. Une simple reformulation échoue.

**Résultat observable :** les sorties reposent uniquement sur des faits traçables et les incertitudes matérielles sont transmises aux contrats suivants.

### C-02 — Validité du contexte déclaré

**Entrée en contexte**

1. Seul un fait fourni ou confirmé explicitement peut entrer dans le contexte déclaré.
2. Un fait réutilisable est mémorisé par défaut après annonce visible ; **Cette fois seulement** le limite à la session.
3. **Passer**, « je ne sais pas », les hypothèses exploratoires, préférences d’interface et textes hors catalogue ne sont pas mémorisés.
4. Une confirmation issue des observations garde la portée étroite de l’objet, période ou action confirmés.

**États et transitions**

- **Actif** : peut influencer une sortie dans sa portée valide.
- **À confirmer** : reste visible mais ne peut influencer aucune sortie.
- **Corrigé** : une nouvelle valeur explicite remplace l’ancienne.
- **Supprimé** : le fait est retiré sans ancienne valeur réactivable.
- **Session** : la valeur pilote seulement la demande courante.

Une correction récente et non ambiguë sur le même fait, la même période et le même périmètre remplace l’ancienne valeur. Si période ou périmètre restent ambigus, le parcours clarifie au lieu de choisir.

**Expiration**

- un fait durable reste actif jusqu’à correction ou suppression ;
- un fait daté expire à sa date de fin ;
- un fait volatil expire à 30, 90 ou 180 jours selon le catalogue ;
- une date de fin explicite plus proche prévaut sur la fenêtre normale ;
- un fait expiré devient à confirmer ; il n’est redemandé que s’il est matériel pour la demande courante.

**Contrôle utilisateur**

Chaque fait reste retrouvable avec valeur, état et dernière confirmation. **Corriger** et **Supprimer** sont disponibles depuis le contexte et depuis toute sortie qui cite le fait.

### C-03 — Incompatibilités et autorité

1. Un fait déclaré actif est présumé vrai.
2. Une observation ne devient une incompatibilité que si elle :
   - se rattache sans ambiguïté au même objet, à la même période et au même périmètre ;
   - satisfait les exigences de preuve de la taxonomie ;
   - rend la valeur déclarée réellement improbable ;
   - peut changer une sortie décisionnelle.
3. Un signal non recevable ou non décisionnel est ignoré ; le fait reste actif sans question.
4. Une incompatibilité recevable expose la valeur mémorisée, sa date, le signal, sa période, son périmètre et le sujet affecté.
5. **Confirmer** maintient ou réactive le fait, date la confirmation et acquitte les observations montrées.
6. Les mêmes observations, un recalcul ou une nouvelle exécution de classification ne rouvrent jamais la question.
7. Après confirmation, seule une preuve directe ou structurelle nouvelle, ou une nouvelle série récurrente entièrement postérieure, peut rouvrir le doute.
8. Une incompatibilité non résolue rend le fait à confirmer et le neutralise uniquement pour le sujet dépendant.

### C-04 — Clarification

Pour chaque fait matériel incertain, le parcours compare les sorties produites par ses valeurs plausibles.

1. **Conseiller directement** si une même recommandation reste valide pour toutes les valeurs plausibles.
2. **Clarifier** seulement si une réponse raisonnablement disponible départage des sorties différentes.
3. Ne poser aucune question si la réponse ne peut changer qu’une formulation ou si l’utilisateur ne peut raisonnablement connaître le fait.
4. Afficher une seule question à la fois et un seul fait par question.
5. Ordonner les questions par levier décisionnel ; à impact égal, privilégier la validité des données, puis les obligations, puis la facilité de réponse.
6. Arrêter dès qu’aucune question restante ne peut changer la réponse.
7. Toujours proposer **Passer**.
8. Ne jamais dépasser trois questions pour une demande de conseil.

Dans le parcours progressif, les recommandations robustes sont immédiatement visibles. La clarification apparaît au point exact du conseil qu’elle bloque, explique en une phrase ce qui peut changer, puis est remplacée au même endroit par la sortie décidée ou un sujet non conclu.

Une clarification d’incompatibilité propose **Confirmer**, **Corriger**, **Cette fois seulement** et **Je ne sais pas / Passer**.

### C-05 — Sorties, personnalisation et abstention

Une sortie est l’un des types suivants :

- **recommandation** : action priorisée, éventuellement accompagnée d’un montant ou d’une échéance dérivable ;
- **conclusion sans action** : aucun écart matériel ne justifie une action ;
- **sujet non conclu** : aucune action robuste n’est défendable sur ce sujet.

Une recommandation valide satisfait simultanément :

1. **sensibilité décisionnelle** : un contrefactuel matériel change la décision lorsqu’il le doit ;
2. **ancrage factuel** : tous les faits porteurs ont une provenance explicite ;
3. **adéquation** : obligations, contraintes et préférences soutenables sont respectées ;
4. **faisabilité** : l’action est possible dans les contraintes connues ;
5. **précision calibrée** : chiffres et échéances sont dérivables ;
6. **droit à l’absence d’action** : aucun problème n’est inventé.

Si seules certaines sorties sont robustes, le parcours produit une réponse sélective. Si aucune recommandation ni conclusion sans action n’est robuste, il s’abstient totalement. Les branches « si… / si… » peuvent expliquer l’abstention, mais ne contiennent ni action priorisée ni montant.

### C-06 — Trace de décision

Chaque recommandation, conclusion sans action ou sujet non conclu porte une trace à deux niveaux.

**Résumé visible**

- action ou conclusion ;
- raison en une phrase ;
- faits matériels avec valeur et provenance **observé** ou **déclaré** ;
- limites de période, périmètre ou fraîcheur qui peuvent changer l’interprétation ;
- état d’incertitude : **Étayé**, **Robuste malgré…** ou **Sujet non conclu**.

Seuls les faits ayant un effet décisionnel sont cités.

**Voir le raisonnement**

1. pour chaque observation : période exacte, comptes inclus, règle ou calcul appliqué ;
2. pour chaque fait déclaré : statut session ou mémorisé, dernière confirmation et validité ;
3. conventions contestables qui affectent le résultat, notamment catégorisation, récurrence, complétude du périmètre et repère budgétaire ;
4. seuils dérivables ou branches qualitatives qui feraient changer la sortie.

**Correction reliée à la source**

- observation : **Voir les transactions**, puis recatégoriser à la source ;
- fait déclaré : **Corriger** ou **Supprimer** ;
- convention ou calcul : **Voir le calcul**, puis corriger l’entrée concernée.

Un fait expiré ou à confirmer ne peut jamais être cité comme preuve active. Le détail n’expose ni narration libre comme seule preuve, ni raisonnement interne brut, ni score probabiliste arbitraire.

## 4. Catalogue fermé du contexte déclaré

Aucun autre type de fait ne peut être demandé ou utilisé comme contexte décisionnel. Tous les faits sont optionnels et ne sont demandés que lorsqu’ils peuvent changer une sortie.

| ID | Famille | Fait permis | Portée et contenu minimal | Cycle |
|---|---|---|---|---|
| **F-01** | Validité des observations | Couverture de la période analysée | Période et périmètre couverts, ou élément pertinent manquant | Daté, limité à la fenêtre analysée |
| **F-02** | Sens des flux | Nature d’une transaction historique précise | Revenu, remboursement, transfert, dépense, paiement de dette ou épargne ; ponctuel/récurrent limité à l’occurrence ou série confirmée | Durable, portée étroite |
| **F-03** | Stock disponible | Réserve liquide non affectée | Montant immédiatement disponible après engagements et affectations connus | Volatil, 30 jours |
| **F-04** | Fonds d’urgence | Plancher de sécurité | Montant ou nombre de mois de dépenses essentielles à protéger | Volatil, 180 jours |
| **F-05** | Revenus | Revenu disponible habituel | Montant et fréquence attendus | Volatil, 90 jours |
| **F-06** | Revenus | Entrée exceptionnelle attendue | Montant et date attendue | Daté |
| **F-07** | Obligations | Obligation récurrente | Montant, fréquence et éventuelle date de fin | Volatil, 90 jours |
| **F-08** | Obligations | Obligation ponctuelle | Montant et échéance | Daté |
| **F-09** | Dettes | Position d’une dette | Solde et éventuel retard, avec libellé neutre | Volatil, 30 jours |
| **F-10** | Dettes | Conditions essentielles d’une dette | Paiement minimum, coût ou taux et éventuelle date de fin | Volatil, 90 jours |
| **F-11** | Objectif | Priorité active | Un objectif courant, sa cible et son échéance éventuelle | Volatil, 180 jours |
| **F-12** | Objectif | Montant déjà affecté à la priorité active | Somme réservée à cet objectif, distincte de la réserve non affectée | Volatil, 30 jours |
| **F-13** | Préférence et faisabilité | Limite financière d’un poste ou d’une action | Plancher, plafond ou montant soutenable rattaché au poste ou à l’action | Volatil, 90 jours |
| **F-14** | Faisabilité | Indisponibilité d’une action jusqu’à une date | Action impossible et date de réexamen | Daté |

### 4.1 Exclusions du catalogue

Sont exclus : situation de vie brute, récit libre, émotions, motivations, causes comportementales, identité détaillée d’un compte ou produit, fiscalité, placements, règle générale déduite d’un marchand, budget cible complet, objectifs secondaires, profil général de contraintes, préférences d’interface, donnée déjà observée avec fiabilité suffisante et toute information ne changeant que l’explication.

Un texte spontané hors catalogue peut être compris pour l’échange courant, mais il n’entre pas dans le contexte décisionnel et n’est pas réutilisé.

## 5. Taxonomie des incompatibilités

### 5.1 Filtre commun

Une présence directement appariée vaut sur son périmètre local. Toute absence ou comparaison agrégée exige une couverture complète et sans trou. Le filtre de matérialité de C-03 s’applique après la recevabilité du signal.

### 5.2 Signaux admis

| ID | Fait concerné | Signal admis | Exigence |
|---|---|---|---|
| **SIG-A01** | F-01 | Preuve de provenance : import incomplet ou échoué, relevé tronqué, compte auparavant inclus devenu absent, nouvelle source explicitement hors périmètre | La preuve touche la période ou le périmètre du conseil ; aucun seuil de volume |
| **SIG-A02** | F-02 | Nouveau lien structurel : contre-écriture, transfert apparié, annulation, remboursement lié, correction du type ou du signe par la source | Le lien porte sur la transaction confirmée |
| **SIG-A03** | F-05 | Revenu récurrent défavorable | 2 cycles attendus complets, consécutifs et appariés ; médiane ou fréquence inférieure d’au moins 20 % |
| **SIG-A04** | F-05 | Revenu récurrent favorable | 3 cycles attendus complets, consécutifs et appariés ; médiane ou fréquence supérieure d’au moins 20 % |
| **SIG-A05** | F-07 | Obligation récurrente défavorable | 2 cycles complets et consécutifs ; médiane ou fréquence supérieure d’au moins 20 % |
| **SIG-A06** | F-07 | Obligation récurrente favorable | 3 cycles complets et consécutifs ; médiane ou fréquence inférieure d’au moins 20 % |
| **SIG-A07** | F-06, F-08 | Opération appariée créant une ambiguïté entre événement attendu, réalisé ou partiel | Écart d’au moins 20 %, ou écart moindre si éviter un double compte change la sortie ; l’absence à échéance relève de l’expiration |
| **SIG-A08** | F-01, F-02 | Nouvelle preuve directe ou structurelle après confirmation | Porte sur l’objet confirmé et peut changer la décision |
| **SIG-A09** | F-05, F-07 | Nouvelle série récurrente après confirmation | 2 cycles défavorables ou 3 favorables, tous entièrement postérieurs à la confirmation |

### 5.3 Signaux explicitement rejetés

| ID | Signal rejeté | Raison observable |
|---|---|---|
| **SIG-R01** | Marchand, catégorie LLM, fréquence ou recatégorisation seuls pour contester F-02 | Aucun lien structurel avec la transaction confirmée |
| **SIG-R02** | Absence ou agrégat sur une couverture incomplète ou trouée | Le périmètre ne permet pas d’établir l’absence |
| **SIG-R03** | Transactions seules pour déduire F-03, F-09, F-10 ou F-12 | Un flux ne reconstitue pas un stock, une affectation ou un contrat |
| **SIG-R04** | Comportement passé pour contester F-04, F-11, F-13 ou F-14 | Un comportement n’annule pas un choix ou une contrainte déclarés |
| **SIG-R05** | Série sous le nombre de cycles requis, écart inférieur à 20 %, ou signal sans effet décisionnel | La preuve est insuffisante ou ne peut changer aucune sortie |

### 5.4 Faits sans signal transactionnel admis

- F-03, F-09, F-10 et F-12 changent par déclaration, correction, expiration ou future source directe couvrant exactement le stock ou contrat.
- F-04, F-11, F-13 et F-14 changent uniquement par nouvelle déclaration explicite, correction, expiration ou suppression.

## 6. Scénarios financiers canoniques

### 6.1 Socle commun

Sauf variation explicitement indiquée :

- revenus observés : **3 000 €/mois** ;
- dépenses essentielles : **1 800 €/mois** ;
- dépenses discrétionnaires : **500 €/mois** ;
- capacité mensuelle : **700 €** ;
- réserve liquide déclarée : **2 000 €** ;
- plancher de sécurité : **5 400 €** ;
- priorité active : **fonds d’urgence** ;
- observations complètes sur la période utile ;
- faits déclarés actifs.

La sortie de référence affecte **700 €/mois** au fonds d’urgence, pour combler **3 400 €** en environ **5 mois**.

Chaque scénario fixe les entrées et leur provenance, la sortie, l’état final des faits, le nombre de questions et la raison auditable.

### S-01 — Conseil robuste ou fondé sur un fait actif

- **Variation :** aucune, ou un fait absent dont toutes les valeurs plausibles laissent la sortie inchangée.
- **Sortie :** recommandation directe de référence. Variante sans écart matériel : conclusion sans action justifiée.
- **État final :** faits actifs inchangés ; un fait réutilisable explicitement fourni peut devenir mémorisé après annonce.
- **Questions :** 0.
- **Raison auditable :** faits matériels, provenances et calcul de l’écart ; aucune incertitude ne change la décision.
- **Couverture primaire :** F-11, T-02, Q-01, ABS-01, X-01, X-02, X-03, X-04, X-09.

### S-02 — Signal irrecevable ou non décisionnel ignoré

- **Variation :** preuve hors objet, couverture incomplète, cycles ou seuil insuffisants, tentative de déduire un stock, contrat ou choix depuis les transactions, ou signal recevable sans effet décisionnel.
- **Sortie :** le conseil robuste reste présentable.
- **État final :** fait déclaré toujours actif.
- **Questions :** 0.
- **Raison auditable :** signal rejeté avec la règle de recevabilité ou de matérialité correspondante.
- **Couverture primaire :** SIG-R05, X-05.

### S-03 — Incompatibilité recevable et matérielle

- **Variation :** F-05 vaut 3 000 €, mais deux cycles complets, consécutifs et appariés montrent 2 300 €, soit une baisse supérieure à 20 % ; le montant soutenable change.
- **Sortie :** une clarification ciblée ; aucun montant dépendant n’est conseillé avant réponse.
- **Question :** expose valeur, confirmation, signal, période, périmètre et sujet ; propose les quatre réponses normatives.
- **État final :** inchangé tant que l’utilisateur n’a pas répondu.
- **Questions :** 1.
- **Raison auditable :** preuve admise et effet sur le montant.
- **Couverture primaire :** F-05, Q-02, Q-09.

### S-04 — Résolution, acquittement et réouverture

À partir de S-03 :

| Réponse ou événement | Sortie | État final |
|---|---|---|
| **Confirmer 3 000 €** | Sortie fondée sur 3 000 € | Actif, confirmation datée, cycles montrés acquittés |
| **Corriger à 2 300 €** | Sortie recalculée | Ancienne valeur remplacée, nouvelle active |
| **Cette fois seulement : 2 300 €** | 2 300 € pilote la session | Réponse de session ; ancien fait mémorisé à confirmer après session |
| **Je ne sais pas / Passer** | Sujet dépendant non conclu | Fait à confirmer et neutralisé |
| **Supprimer** | Sortie dépendante retirée ou recalculée sans le fait | Fait supprimé sans ancienne valeur réactivable |
| Même observation ou recalcul | Aucune nouvelle question | État inchangé |
| Nouvelle preuve recevable | Nouvelle clarification seulement si décisionnelle | Doute rouvert |
| Nouvelle réponse explicite, récente et non ambiguë | Sortie recalculée | Valeur corrigée |
| Nouvelle réponse à portée ambiguë | Clarification | Aucun remplacement silencieux |

- **Questions :** la résolution consomme la question déjà posée ; une réouverture recevable peut en consommer une lors d’une nouvelle demande.
- **Raison auditable :** branche choisie, état résultant et observations acquittées ou nouvelles.
- **Couverture primaire :** T-01, T-03, T-04, T-05, T-07, T-08, T-09, T-10, Q-07, X-07, X-08.

### S-05 — Expiration matérielle ou non

- **Variation :** réserve à J+31, flux ou limite à J+91, priorité à J+181, fait daté après échéance ou fait durable inchangé.
- **Sortie :** le fait expiré n’influence jamais silencieusement le conseil. Une clarification est posée si la sortie en dépend ; sinon aucune question.
- **État final :** fait expiré à confirmer ; durable toujours actif.
- **Questions :** 1 si matériel, 0 sinon.
- **Raison auditable :** cycle, date de dernière confirmation, fenêtre ou échéance et effet décisionnel.
- **Couverture primaire :** T-06, Q-10, E-07.

### S-06 — Ordre progressif et plafond de trois

- **Variation :** quatre incertitudes utiles simultanées : couverture, obligation récurrente, revenu habituel et plancher de sécurité.
- **Sortie :** recommandations déjà robustes visibles ; sujets dépendants non conclus tant qu’ils ne sont pas tranchés.
- **Ordre :** levier décisionnel, puis validité des données, obligations et facilité à impact égal.
- **État final :** seuls les faits effectivement répondus changent ; la quatrième incertitude reste non résolue.
- **Questions :** exactement 3 au maximum, une à la fois ; arrêt plus tôt si les réponses restantes ne peuvent plus changer la sortie.
- **Raison auditable :** levier de chaque question, ordre et motif d’arrêt.
- **Couverture primaire :** Q-04, Q-05, Q-06, Q-08.

### S-07 — Abstention sélective

- **Variation :** un paiement minimum exigible est robuste et faisable ; le montant d’épargne dépend d’un fait expiré, contesté ou passé.
- **Sortie :** recommandation du paiement minimum ; épargne marquée **Sujet non conclu**. Les branches conditionnelles restent explicatives et non prescriptives.
- **État final :** fait dépendant à confirmer ou sans réponse ; fait du paiement actif.
- **Questions :** nombre déjà consommé par la clarification, compris entre 0 et 3 selon la cause.
- **Raison auditable :** indépendance du paiement, fait manquant pour l’épargne et effet de l’incertitude.
- **Couverture primaire :** ABS-02, ABS-04, X-06.

### S-08 — Abstention totale

- **Variation :** couverture insuffisante, aucun fait actif ne tranche et aucune réponse utile n’est disponible après Passer ou épuisement du quota.
- **Sortie :** aucune recommandation et aucune conclusion sans action ; limites et branches conditionnelles seulement.
- **État final :** faits contestés ou expirés à confirmer ; aucune hypothèse créée.
- **Questions :** de 0 à 3 selon disponibilité et quota.
- **Raison auditable :** faits manquants, impossibilité de clarifier utilement et absence de sortie robuste.
- **Couverture primaire :** Q-03, ABS-03, X-10.

### 6.2 Variantes obligatoires

| ID | Variante | Résultat observable | Couverture primaire |
|---|---|---|---|
| **V-PROV** | Import incomplet ou tronqué ; absence sans preuve pertinente | Une preuve locale peut contester F-01 ; une absence sans couverture est rejetée | F-01, SIG-A01, SIG-R02 |
| **V-TRANS** | Contre-écriture, transfert, annulation, remboursement lié ou correction source ; marchand, fréquence ou recatégorisation seuls | Le lien structurel conteste F-02 ; les indices seuls sont rejetés | F-02, SIG-A02, SIG-R01 |
| **V-FLOW-DOWN** | 2 cycles complets défavorables, écart médian ou fréquence ≥ 20 % | Incompatibilité admise pour revenu plus faible ou obligation plus élevée | F-07, SIG-A03, SIG-A05 |
| **V-FLOW-UP** | 3 cycles complets favorables, même seuil ; 2 cycles insuffisants | Incompatibilité admise seulement au troisième cycle | SIG-A04, SIG-A06 |
| **V-ONEOFF** | Événement apparié, écart ≥ 20 % ou risque matériel de double compte ; absence à échéance | Clarification sur réalisé/partiel ; absence traitée par expiration | F-06, F-08, SIG-A07 |
| **V-STOCK** | Transactions tentant d’inférer stocks, affectations ou contrats | Aucun fait concerné n’est contesté | F-03, F-09, F-10, F-12, SIG-R03 |
| **V-CHOICE** | Comportement tentant d’inférer choix ou contraintes | Aucun choix ni contrainte n’est contesté | F-04, F-13, F-14, SIG-R04 |
| **V-REOPEN** | Preuve directe ou structurelle nouvelle ; série entièrement postérieure à confirmation | Réouverture uniquement avec preuve nouvelle et effet décisionnel | SIG-A08, SIG-A09 |
| **V-FRESH** | 30, 90, 180 jours ; date explicite plus précoce ; durable sans expiration | Transition de validité conforme au cycle | E-01, E-02, E-03, E-04, E-05, E-06 |

F-11 est couvert par S-01, où la priorité active fonde la trajectoire sans supplanter les obligations.

## 7. Registre fermé et matrice de traçabilité

### 7.1 Inventaire normatif

Les identifiants ci-dessous forment l’inventaire fermé. Tout nouvel élément normatif exige une nouvelle version du présent document et une couverture primaire unique.

#### Transitions d’état

| ID | Obligation observable |
|---|---|
| **T-01** | « Cette fois seulement » crée une réponse limitée à la session. |
| **T-02** | Un fait réutilisable explicitement fourni devient mémorisé après annonce visible. |
| **T-03** | Confirmer maintient ou réactive le fait, date la confirmation et acquitte le signal montré. |
| **T-04** | Corriger remplace la valeur active. |
| **T-05** | Supprimer retire le fait sans valeur ancienne réactivable. |
| **T-06** | Expirer rend le fait à confirmer et incapable d’influencer une sortie. |
| **T-07** | Passer ou ne pas savoir face à une incompatibilité rend le fait à confirmer. |
| **T-08** | Une réponse de session contradictoire rend l’ancien fait mémorisé à confirmer après la session. |
| **T-09** | Une réponse explicite plus récente, sur même fait, période et périmètre, corrige sans ambiguïté. |
| **T-10** | Correction ou suppression retire ou recalcule immédiatement toute sortie dépendante. |

#### Branches de clarification

| ID | Obligation observable |
|---|---|
| **Q-01** | Une recommandation robuste est produite sans question. |
| **Q-02** | Une question n’est posée que si ses réponses plausibles changent la sortie. |
| **Q-03** | Une incertitude non raisonnablement répondable ne déclenche pas de question. |
| **Q-04** | Une seule question et un seul fait sont visibles à la fois. |
| **Q-05** | L’ordre suit le levier décisionnel puis les critères de départage. |
| **Q-06** | Les questions cessent dès qu’aucune réponse restante ne change la sortie. |
| **Q-07** | Passer reste toujours disponible et ne crée aucun fait déclaré. |
| **Q-08** | Une demande de conseil consomme au plus trois questions. |
| **Q-09** | Une incompatibilité expose les preuves et quatre réponses normatives. |
| **Q-10** | Un fait expiré n’est redemandé que s’il est matériel pour la sortie courante. |

#### Règles d’expiration

| ID | Obligation observable |
|---|---|
| **E-01** | Un fait daté expire à sa date de fin. |
| **E-02** | Une date explicite plus précoce prévaut sur toute fenêtre normale. |
| **E-03** | Une position courante expire après 30 jours. |
| **E-04** | Un flux, une condition ou une limite récurrente expire après 90 jours. |
| **E-05** | Une priorité ou préférence expire après 180 jours. |
| **E-06** | Un fait durable n’expire pas avec le temps. |
| **E-07** | Un fait expiré reste visible, inactif, et n’est reconfirmé que si matériel. |

#### Branches d’abstention

| ID | Obligation observable |
|---|---|
| **ABS-01** | Aucun écart matériel établi produit une conclusion sans action justifiée. |
| **ABS-02** | Une réponse sélective conserve les recommandations indépendantes robustes. |
| **ABS-03** | L’absence de toute sortie robuste produit une abstention totale. |
| **ABS-04** | Les branches conditionnelles d’une abstention ne priorisent ni action ni montant. |

#### Branches explicables

| ID | Obligation observable |
|---|---|
| **X-01** | Chaque type de sortie porte une trace de décision. |
| **X-02** | Le résumé montre sortie, raison, faits matériels, provenance, limites matérielles et état d’incertitude. |
| **X-03** | Le détail observé montre période, comptes et règle ou calcul. |
| **X-04** | Le détail déclaré montre statut, confirmation et validité. |
| **X-05** | Les conventions contestables et seuils ou branches qui changent la sortie sont visibles. |
| **X-06** | L’incertitude est exprimée par Étayé, Robuste malgré… ou Sujet non conclu. |
| **X-07** | Chaque preuve renvoie vers l’action de correction de sa source. |
| **X-08** | Une correction rend immédiatement caduque la sortie précédente. |
| **X-09** | La trace cite les causes décisionnelles, pas l’inventaire des entrées. |
| **X-10** | Aucun raisonnement interne brut ni score de confiance arbitraire n’est exposé. |

Les faits F-01 à F-14 et les signaux SIG-A01 à SIG-A09 et SIG-R01 à SIG-R05 sont définis respectivement aux sections 4 et 5 ; ils font partie du même inventaire fermé.

### 7.2 Registre de couverture primaire

| ID | Catégorie | Contrat source | Propriétaire primaire | Variante | Résultat attendu |
|---|---|---|---|---|---|
| F-01 | Fait | C-01 | V-PROV | Provenance | Couverture qualifiée ou contestée par preuve directe |
| F-02 | Fait | C-01 | V-TRANS | Transaction | Nature contestée uniquement par lien structurel |
| F-03 | Fait | C-02 | V-STOCK | Stock | Réserve non inférée depuis les flux |
| F-04 | Fait | C-02 | V-CHOICE | Choix | Plancher non contesté par comportement |
| F-05 | Fait | C-03 | S-03 | — | Revenu contesté par série recevable |
| F-06 | Fait | C-02 | V-ONEOFF | Événement | Entrée attendue clarifiée sans double compte |
| F-07 | Fait | C-03 | V-FLOW-DOWN | Flux défavorable | Obligation contestée après deux cycles |
| F-08 | Fait | C-02 | V-ONEOFF | Événement | Obligation ponctuelle clarifiée |
| F-09 | Fait | C-02 | V-STOCK | Stock | Position de dette non inférée |
| F-10 | Fait | C-02 | V-STOCK | Contrat | Conditions de dette non inférées |
| F-11 | Fait | C-05 | S-01 | — | Priorité active oriente la trajectoire |
| F-12 | Fait | C-02 | V-STOCK | Affectation | Montant affecté non inféré |
| F-13 | Fait | C-05 | V-CHOICE | Contrainte | Limite soutenable non contredite par comportement |
| F-14 | Fait | C-05 | V-CHOICE | Contrainte | Indisponibilité corrigée seulement explicitement |
| SIG-A01 | Signal admis | C-03 | V-PROV | Provenance | Preuve directe recevable |
| SIG-A02 | Signal admis | C-03 | V-TRANS | Transaction | Lien structurel recevable |
| SIG-A03 | Signal admis | C-03 | V-FLOW-DOWN | Flux défavorable | Revenu plus faible après deux cycles |
| SIG-A04 | Signal admis | C-03 | V-FLOW-UP | Flux favorable | Revenu plus élevé après trois cycles |
| SIG-A05 | Signal admis | C-03 | V-FLOW-DOWN | Flux défavorable | Obligation plus forte après deux cycles |
| SIG-A06 | Signal admis | C-03 | V-FLOW-UP | Flux favorable | Obligation plus faible après trois cycles |
| SIG-A07 | Signal admis | C-03 | V-ONEOFF | Événement | Réalisation ou montant clarifié |
| SIG-A08 | Signal admis | C-03 | V-REOPEN | Réouverture | Nouvelle preuve directe peut rouvrir |
| SIG-A09 | Signal admis | C-03 | V-REOPEN | Réouverture | Nouvelle série postérieure peut rouvrir |
| SIG-R01 | Signal rejeté | C-03 | V-TRANS | Transaction | Indice sans lien structurel rejeté |
| SIG-R02 | Signal rejeté | C-01 | V-PROV | Provenance | Absence sans couverture rejetée |
| SIG-R03 | Signal rejeté | C-03 | V-STOCK | Stock | Inférence de stock ou contrat rejetée |
| SIG-R04 | Signal rejeté | C-03 | V-CHOICE | Choix | Inférence de préférence rejetée |
| SIG-R05 | Signal rejeté | C-03 | S-02 | — | Preuve ou effet insuffisant ignoré |
| T-01 | Transition | C-02 | S-04 | Session | Valeur limitée à la session |
| T-02 | Transition | C-02 | S-01 | — | Fait réutilisable mémorisé |
| T-03 | Transition | C-03 | S-04 | Confirmation | Fait maintenu et signal acquitté |
| T-04 | Transition | C-02 | S-04 | Correction | Valeur remplacée |
| T-05 | Transition | C-02 | S-04 | Suppression | Fait retiré |
| T-06 | Transition | C-02 | S-05 | Expiration | Fait rendu à confirmer |
| T-07 | Transition | C-03 | S-04 | Passer | Fait contesté neutralisé |
| T-08 | Transition | C-03 | S-04 | Session contradictoire | Ancien fait rendu à confirmer |
| T-09 | Transition | C-03 | S-04 | Réponse récente | Correction non ambiguë |
| T-10 | Transition | C-02 | S-04 | Invalidation | Sortie retirée ou recalculée |
| Q-01 | Clarification | C-04 | S-01 | — | Conseil robuste sans question |
| Q-02 | Clarification | C-04 | S-03 | — | Question seulement si décisionnelle |
| Q-03 | Clarification | C-04 | S-08 | — | Pas de question sans réponse utile |
| Q-04 | Clarification | C-04 | S-06 | Progression | Une question à la fois |
| Q-05 | Clarification | C-04 | S-06 | Ordre | Levier et départage respectés |
| Q-06 | Clarification | C-04 | S-06 | Arrêt | Arrêt dès absence d’effet restant |
| Q-07 | Clarification | C-04 | S-04 | Passer | Omission disponible, rien mémorisé |
| Q-08 | Clarification | C-04 | S-06 | Quota | Plafond de trois respecté |
| Q-09 | Clarification | C-04 | S-03 | Contradiction | Preuves et quatre réponses visibles |
| Q-10 | Clarification | C-04 | S-05 | Expiration | Reconfirmation seulement si matérielle |
| E-01 | Expiration | C-02 | V-FRESH | Daté | Expiration à date |
| E-02 | Expiration | C-02 | V-FRESH | Date anticipée | Date explicite prioritaire |
| E-03 | Expiration | C-02 | V-FRESH | 30 jours | Position rendue à confirmer |
| E-04 | Expiration | C-02 | V-FRESH | 90 jours | Flux ou limite rendu à confirmer |
| E-05 | Expiration | C-02 | V-FRESH | 180 jours | Priorité ou préférence rendue à confirmer |
| E-06 | Expiration | C-02 | V-FRESH | Durable | Aucune expiration temporelle |
| E-07 | Expiration | C-02 | S-05 | — | Fait visible, inactif, redemandé si matériel |
| ABS-01 | Abstention | C-05 | S-01 | Sans écart | Conclusion sans action |
| ABS-02 | Abstention | C-05 | S-07 | Sélective | Recommandations robustes conservées |
| ABS-03 | Abstention | C-05 | S-08 | Totale | Aucune recommandation non étayée |
| ABS-04 | Abstention | C-05 | S-07 | Conditionnelle | Explication sans prescription |
| X-01 | Trace | C-06 | S-01 | — | Trace sur chaque sortie |
| X-02 | Trace | C-06 | S-01 | Résumé | Causes et limites visibles |
| X-03 | Trace | C-06 | S-01 | Observation | Période, comptes et calcul visibles |
| X-04 | Trace | C-06 | S-01 | Déclaration | Statut, confirmation et validité visibles |
| X-05 | Trace | C-06 | S-02 | Convention | Convention et seuil contestables |
| X-06 | Trace | C-06 | S-07 | Incertitude | État exprimé par son effet |
| X-07 | Trace | C-06 | S-04 | Correction | Preuve reliée à sa source |
| X-08 | Trace | C-06 | S-04 | Invalidation | Ancienne sortie immédiatement caduque |
| X-09 | Trace | C-06 | S-01 | Sélection | Seuls les faits décisionnels sont cités |
| X-10 | Trace | C-06 | S-08 | Limite | Aucun raisonnement brut ni score arbitraire |

### 7.3 Matrice inverse par propriétaire

| Propriétaire primaire | Identifiants possédés |
|---|---|
| S-01 | F-11, T-02, Q-01, ABS-01, X-01, X-02, X-03, X-04, X-09 |
| S-02 | SIG-R05, X-05 |
| S-03 | F-05, Q-02, Q-09 |
| S-04 | T-01, T-03, T-04, T-05, T-07, T-08, T-09, T-10, Q-07, X-07, X-08 |
| S-05 | T-06, Q-10, E-07 |
| S-06 | Q-04, Q-05, Q-06, Q-08 |
| S-07 | ABS-02, ABS-04, X-06 |
| S-08 | Q-03, ABS-03, X-10 |
| V-PROV | F-01, SIG-A01, SIG-R02 |
| V-TRANS | F-02, SIG-A02, SIG-R01 |
| V-FLOW-DOWN | F-07, SIG-A03, SIG-A05 |
| V-FLOW-UP | SIG-A04, SIG-A06 |
| V-ONEOFF | F-06, F-08, SIG-A07 |
| V-STOCK | F-03, F-09, F-10, F-12, SIG-R03 |
| V-CHOICE | F-04, F-13, F-14, SIG-R04 |
| V-REOPEN | SIG-A08, SIG-A09 |
| V-FRESH | E-01, E-02, E-03, E-04, E-05, E-06 |

### 7.4 Contrôle de complétude

| Catégorie | Inventorié | Couvert une fois |
|---|---:|---:|
| Faits du catalogue | 14 | 14 |
| Signaux admis ou rejetés | 14 | 14 |
| Transitions d’état | 10 | 10 |
| Branches de clarification | 10 | 10 |
| Règles d’expiration | 7 | 7 |
| Branches d’abstention | 4 | 4 |
| Branches explicables | 10 | 10 |
| **Total** | **69** | **69** |

La matrice satisfait les contrôles suivants :

1. les 69 identifiants de l’inventaire ont chacun une ligne de registre ;
2. chaque identifiant possède exactement un scénario ou une variante propriétaire ;
3. aucun identifiant n’est inconnu, orphelin ou doublement propriétaire ;
4. chacun des huit scénarios et chacune des neuf variantes possède une couverture primaire ;
5. chaque scénario fixe entrées et provenances, sortie, état final, consommation du quota et raison auditable ;
6. chacun des contrats C-01 à C-06 possède au moins un identifiant couvert ;
7. aucune exigence d’architecture ou d’implémentation ne complète artificiellement la couverture.

## Provenance des décisions

- [Inventorier les hypothèses du conseil actuel](https://github.com/schalappe/weathflow/issues/35)
- [Définir ce qui rend un conseil personnalisé](https://github.com/schalappe/weathflow/issues/36)
- [Décider quand demander une clarification](https://github.com/schalappe/weathflow/issues/37#issuecomment-5156426215)
- [Décider ce que le contexte déclaré mémorise](https://github.com/schalappe/weathflow/issues/38#issuecomment-5156556010)
- [Prototyper le parcours de clarification](https://github.com/schalappe/weathflow/issues/39#issuecomment-5156746794)
- [Décider comment traiter un contexte contradictoire ou périmé](https://github.com/schalappe/weathflow/issues/40#issuecomment-5157121130)
- [Rendre le conseil explicable](https://github.com/schalappe/weathflow/issues/41#issuecomment-5157355441)
- [Définir le contexte déclaré minimal](https://github.com/schalappe/weathflow/issues/42#issuecomment-5157457626)
- [Définir les signaux d’incompatibilité du contexte déclaré](https://github.com/schalappe/weathflow/issues/43#issuecomment-5157767672)
- [Définir les scénarios financiers de validation](https://github.com/schalappe/weathflow/issues/44#issuecomment-5157838989)
- [Définir l’actif final de spécification](https://github.com/schalappe/weathflow/issues/45#issuecomment-5157914588)
