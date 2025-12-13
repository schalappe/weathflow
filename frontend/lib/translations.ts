// [>]: Centralized French translations for the entire frontend.
// All UI text is in French as the sole language of the application.

export const t = {
  // Navigation & Layout
  nav: {
    dashboard: "Tableau de bord",
    import: "Importer",
    history: "Historique",
  },
  brand: {
    name: "Money Map",
    tagline: "50 / 30 / 20",
    footer: "Money Map Manager",
    footerTagline: "Construit pour la méthode 50/30/20",
  },
  meta: {
    title: "Money Map Manager",
    description: "Finances personnelles avec la méthode 50/30/20",
  },

  // Money Map Categories
  categories: {
    INCOME: "Revenus",
    CORE: "Essentiel",
    CHOICE: "Plaisir",
    COMPOUND: "Épargne",
    EXCLUDED: "Exclu",
  },

  // Subcategories
  subcategories: {
    // INCOME
    Job: "Salaire",
    // CORE
    Housing: "Logement",
    Groceries: "Courses",
    Utilities: "Charges",
    Healthcare: "Santé",
    Transportation: "Transport",
    "Basic clothing": "Vêtements basiques",
    "Phone and internet": "Téléphone et internet",
    Insurance: "Assurance",
    "Debt payments": "Remboursement de dettes",
    // CHOICE
    "Dining out": "Restaurant",
    Entertainment: "Divertissement",
    "Travel and vacations": "Voyages et vacances",
    "Electronics and gadgets": "Électronique",
    "Hobby supplies": "Loisirs",
    "Fancy clothing": "Vêtements de luxe",
    "Subscription services": "Abonnements",
    "Home decor": "Décoration",
    Gifts: "Cadeaux",
    // COMPOUND
    "Emergency Fund": "Fonds d'urgence",
    "Education Fund": "Épargne études",
    Investments: "Investissements",
    Other: "Autre",
  },

  // Dashboard
  dashboard: {
    title: "Tableau de bord",
    subtitle: "Votre aperçu Money Map pour la période sélectionnée",
    empty: {
      title: "Aucune donnée",
      description:
        "Importez votre premier export CSV Bankin' pour voir votre tableau de bord Money Map et commencer à suivre votre budget 50/30/20.",
      button: "Importer des transactions",
    },
    retry: "Réessayer",
  },

  // Score Card
  score: {
    currentPeriod: "Période actuelle",
    descriptions: {
      3: "Excellent contrôle budgétaire",
      2: "Bonne progression, peut mieux faire",
      1: "Certaines catégories à surveiller",
      0: "Objectifs budgétaires non atteints",
    },
    labels: {
      Great: "Excellent",
      Okay: "Correct",
      "Need Improvement": "À améliorer",
      Poor: "Insuffisant",
    },
  },

  // Metric Cards
  metrics: {
    Income: "Revenus",
    Core: "Essentiel",
    Choice: "Plaisir",
    Compound: "Épargne",
    target: "Objectif",
    ofIncome: "des revenus",
    onTrack: "Conforme",
    overTarget: "Dépassé",
    savings: "Épargne",
    withdrawal: "Retrait",
    thresholdMet: "Objectif atteint",
    thresholdExceeded: "Objectif dépassé",
  },

  // Spending Pie Chart
  spendingChart: {
    title: "Répartition des dépenses",
    selectCategory: "Sélectionner une catégorie",
    empty: "Aucune donnée de dépenses",
    amount: "Montant",
  },

  // Transaction Table
  transactions: {
    title: "Transactions",
    total: "total",
    headers: {
      date: "Date",
      description: "Description",
      amount: "Montant",
      category: "Catégorie",
    },
    empty: "Aucune transaction",
    noMatch: "Aucune transaction ne correspond à vos filtres",
    clearFilters: "Effacer les filtres",
    manuallyCorrected: "Corrigée manuellement",
  },

  // Transaction Filters
  filters: {
    allCategories: "Toutes les catégories",
    categories: "Catégories",
    filterByCategory: "Filtrer par catégorie",
    from: "Du",
    to: "Au",
    search: "Rechercher...",
    clear: "Effacer",
  },

  // Transaction Edit Modal
  editModal: {
    title: "Modifier la transaction",
    description: "Mettre à jour la catégorie de cette transaction.",
    labels: {
      description: "Description",
      amount: "Montant",
      date: "Date",
    },
    categoryType: "Type de catégorie",
    subcategory: "Sous-catégorie",
    selectCategoryType: "Sélectionner un type",
    selectSubcategory: "Sélectionner une sous-catégorie",
    cancel: "Annuler",
    save: "Enregistrer",
  },

  // Month Selector
  monthSelector: {
    label: "Sélectionner le mois",
    placeholder: "Sélectionner le mois",
  },

  // Export
  export: {
    exporting: "Export...",
    success: "exporté avec succès",
    error: "Échec de l'export",
  },

  // Import Page
  import: {
    title: "Importer des transactions",
    subtitle:
      "Téléchargez votre export CSV Bankin' pour catégoriser vos transactions avec l'IA",
    retry: "Réessayer",
    analyzing: "Analyse du fichier...",
    detectingMonths: "Détection des mois et transactions",
  },

  // File Dropzone
  dropzone: {
    invalidFile:
      "Type de fichier invalide. Veuillez sélectionner un fichier CSV (extension .csv requise).",
    dropToUpload: "Déposez pour télécharger",
    dragHere: "Glissez votre fichier CSV ici",
    orClick: "ou cliquez pour sélectionner",
    clickToReplace: "Cliquez ou glissez pour remplacer",
    acceptedFormat: "Format accepté : .csv",
  },

  // Month Preview Table
  monthPreview: {
    headers: {
      month: "Mois",
      transactions: "Transactions",
      income: "Revenus",
      expenses: "Dépenses",
    },
    selectAll: "Tout sélectionner",
    deselectAll: "Tout désélectionner",
    selected: "mois sélectionné(s)",
    of: "sur",
  },

  // Import Options
  importOptions: {
    label: "Mode d'import",
    merge: {
      title: "Fusionner",
      description: "Ajouter les nouvelles transactions, ignorer les doublons",
    },
    replace: {
      title: "Remplacer",
      description:
        "Supprimer les données existantes pour les mois sélectionnés",
    },
  },

  // File Analysis
  fileAnalysis: {
    title: "Analyse du fichier",
    transactions: "transactions sur",
    months: "mois",
    startOver: "Recommencer",
    categorize: "Catégoriser avec l'IA",
  },

  // Progress Panel
  progress: {
    processing: "Traitement de",
    month: "mois",
    months: "mois",
    note: "Cela peut prendre un moment selon le nombre de transactions",
    cancel: "Annuler",
  },

  // Results Summary
  results: {
    complete: "Import terminé !",
    transactionsCategorized: "transactions catégorisées sur",
    apiCalls: "appels API",
    monthsNotFound: "Certains mois n'ont pas été trouvés dans le CSV",
    viewTransactions: "Voir les transactions pour vérifier",
    comingSoon: "Bientôt disponible dans le Tableau de bord",
    finish: "Terminer l'import",
    score: "Score",
    lowConfidence: "faible confiance",
    skipped: "ignorée(s) (erreur de catégorisation)",
  },

  // History Page
  history: {
    title: "Historique",
    subtitle:
      "Suivez l'évolution de votre budget et obtenez des conseils personnalisés",
    empty: {
      title: "Aucune donnée historique",
      description:
        "Importez vos transactions pour voir l'évolution de votre budget et recevoir des conseils personnalisés.",
      button: "Importer des transactions",
    },
    retry: "Réessayer",
  },

  // Period Selector
  periods: {
    3: "3 mois",
    6: "6 mois",
    12: "12 mois",
    0: "Tout",
  },

  // Score Chart
  scoreChart: {
    title: "Évolution du score",
    allTime: "Performance globale",
    lastMonth: "Performance du mois dernier",
    lastMonths: "Performance des {n} derniers mois",
    empty: "Aucune donnée historique disponible",
    error: "Impossible d'afficher le graphique",
    tooltipScore: "Score",
  },

  // Breakdown Chart
  breakdownChart: {
    title: "Répartition des dépenses",
    subtitle: "Distribution mensuelle par catégorie",
    empty: "Aucune donnée de dépenses disponible",
    error: "Impossible d'afficher le graphique",
  },

  // Advice Panel
  advice: {
    title: "Conseils personnalisés",
    subtitle: "Recommandations IA basées sur vos habitudes de dépenses",
    empty: {
      title: "Aucun conseil disponible",
      description:
        "Générez des conseils personnalisés basés sur vos 3 derniers mois de transactions.",
      button: "Générer des conseils",
    },
    generating: "Génération...",
    sections: {
      analysis: "Analyse des tendances",
      problems: "Points de vigilance",
      recommendations: "Recommandations",
      encouragement: "Continuez comme ça !",
    },
    generated: "Généré",
    regenerate: "Régénérer",
    regenerating: "Régénération...",
    retry: "Réessayer",
    importData: "Importer des données",
    loadError: "Impossible de charger les conseils",
    generateError: "Impossible de générer les conseils",
  },

  // Common
  common: {
    loading: "Chargement...",
    error: "Une erreur est survenue",
    retry: "Réessayer",
    cancel: "Annuler",
    save: "Enregistrer",
    close: "Fermer",
    select: "Sélectionner",
    of: "sur",
  },

  // Error Boundary
  errorBoundary: {
    title: "Une erreur est survenue",
    description: "Une erreur inattendue s'est produite. Veuillez réessayer.",
    retry: "Réessayer",
  },
} as const;

// [>]: Type-safe translation access.
export type TranslationKey = keyof typeof t;
