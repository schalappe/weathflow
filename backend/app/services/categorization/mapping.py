"""Deterministic category mapping for Bankin' to Money Map conversion."""

from typing import ClassVar

from app.db.enums import MoneyMapType


class CategoryMapping:
    """
    Maps Bankin' categories to Money Map categories.

    Provides deterministic mappings for well-known category combinations
    and internal transfer detection to reduce Claude API calls.

    Examples
    --------
    >>> result = CategoryMapping.get_deterministic_category("Alimentation & Restau.", "Supermarché / Epicerie")
    >>> result
    (MoneyMapType.CORE, "Groceries")

    >>> CategoryMapping.is_internal_transfer("Virement interne vers Livret A")
    True
    """

    # ##>: Mapping from (Bankin category, Bankin subcategory) to (MoneyMapType, subcategory).
    BANKIN_TO_MONEYMAP: ClassVar[dict[tuple[str, str], tuple[MoneyMapType, str]]] = {
        # Income
        ("Entrées d'argent", "Salaires"): (MoneyMapType.INCOME, "Job"),
        ("Entrées d'argent", "Primes"): (MoneyMapType.INCOME, "Job"),
        ("Entrées d'argent", "Dividendes"): (MoneyMapType.INCOME, "Investments"),
        ("Entrées d'argent", "Intérêts"): (MoneyMapType.INCOME, "Investments"),
        ("Entrées d'argent", "Revenus locatifs"): (MoneyMapType.INCOME, "Other"),
        ("Entrées d'argent", "Remboursements"): (MoneyMapType.INCOME, "Reimbursements"),
        ("Santé", "Remboursement mutuelle"): (MoneyMapType.INCOME, "Reimbursements"),
        ("Santé", "Remboursement Sécu"): (MoneyMapType.INCOME, "Reimbursements"),
        # Excluded - Internal transfers
        ("Entrées d'argent", "Virements internes"): (MoneyMapType.EXCLUDED, ""),
        ("Entrées d'argent", "Economies"): (MoneyMapType.EXCLUDED, ""),
        ("Retraits, Chq. et Vir.", "Virements internes"): (MoneyMapType.EXCLUDED, ""),
        ("Retraits, Chq. et Vir.", "Virements"): (MoneyMapType.EXCLUDED, ""),
        # Core - Food
        ("Alimentation & Restau.", "Supermarché / Epicerie"): (MoneyMapType.CORE, "Groceries"),
        ("Alimentation & Restau.", "Supermarché"): (MoneyMapType.CORE, "Groceries"),
        ("Alimentation & Restau.", "Epicerie"): (MoneyMapType.CORE, "Groceries"),
        # Core - Transportation
        ("Transport", "Transports en commun"): (MoneyMapType.CORE, "Transportation"),
        ("Transport", "Essence"): (MoneyMapType.CORE, "Transportation"),
        ("Transport", "Parking"): (MoneyMapType.CORE, "Transportation"),
        ("Transport", "Péage"): (MoneyMapType.CORE, "Transportation"),
        ("Transport", "Entretien véhicule"): (MoneyMapType.CORE, "Transportation"),
        # Core - Housing
        ("Logement", "Loyer"): (MoneyMapType.CORE, "Housing"),
        ("Logement", "Charges"): (MoneyMapType.CORE, "Utilities"),
        ("Logement", "Électricité"): (MoneyMapType.CORE, "Utilities"),
        ("Logement", "Gaz"): (MoneyMapType.CORE, "Utilities"),
        ("Logement", "Eau"): (MoneyMapType.CORE, "Utilities"),
        # Core - Healthcare
        ("Santé", "Pharmacie"): (MoneyMapType.CORE, "Healthcare"),
        ("Santé", "Médecin"): (MoneyMapType.CORE, "Healthcare"),
        ("Santé", "Mutuelle"): (MoneyMapType.CORE, "Healthcare"),
        ("Santé", "Dentiste"): (MoneyMapType.CORE, "Healthcare"),
        ("Santé", "Opticien"): (MoneyMapType.CORE, "Healthcare"),
        # Core - Insurance
        ("Assurances", "Assurance habitation"): (MoneyMapType.CORE, "Insurance"),
        ("Assurances", "Assurance auto"): (MoneyMapType.CORE, "Insurance"),
        ("Assurances", "Assurance vie"): (MoneyMapType.CORE, "Insurance"),
        # Core - Phone and Internet
        ("Abonnements", "Téléphone"): (MoneyMapType.CORE, "Phone and internet"),
        ("Abonnements", "Internet"): (MoneyMapType.CORE, "Phone and internet"),
        ("Téléphone", "Forfait"): (MoneyMapType.CORE, "Phone and internet"),
        # Choice - Dining out
        ("Alimentation & Restau.", "Fast foods"): (MoneyMapType.CHOICE, "Dining out"),
        ("Alimentation & Restau.", "Sortie au restaurant"): (MoneyMapType.CHOICE, "Dining out"),
        ("Alimentation & Restau.", "Restaurant"): (MoneyMapType.CHOICE, "Dining out"),
        ("Alimentation & Restau.", "Café"): (MoneyMapType.CHOICE, "Dining out"),
        ("Loisirs & Sorties", "Sortie au restaurant"): (MoneyMapType.CHOICE, "Dining out"),
        ("Loisirs & Sorties", "Bars / Clubs"): (MoneyMapType.CHOICE, "Entertainment"),
        # Choice - Entertainment
        ("Loisirs & Sorties", "Cinéma"): (MoneyMapType.CHOICE, "Entertainment"),
        ("Loisirs & Sorties", "Concerts"): (MoneyMapType.CHOICE, "Entertainment"),
        ("Loisirs & Sorties", "Sport"): (MoneyMapType.CHOICE, "Hobby supplies"),
        # Choice - Subscriptions
        ("Abonnements", "Câble / Satellite"): (MoneyMapType.CHOICE, "Subscription services"),
        ("Abonnements", "Abonnements - Autres"): (MoneyMapType.CHOICE, "Subscription services"),
        ("Abonnements", "Streaming"): (MoneyMapType.CHOICE, "Subscription services"),
        ("Dépenses pro", "Services en ligne"): (MoneyMapType.CHOICE, "Subscription services"),
        # Choice - Shopping
        ("Shopping", "Vêtements"): (MoneyMapType.CHOICE, "Fancy clothing"),
        ("Shopping", "High-Tech"): (MoneyMapType.CHOICE, "Electronics and gadgets"),
        ("Shopping", "Électronique"): (MoneyMapType.CHOICE, "Electronics and gadgets"),
        ("Shopping", "Décoration"): (MoneyMapType.CHOICE, "Home decor"),
        ("Shopping", "Cadeaux"): (MoneyMapType.CHOICE, "Gifts"),
        ("Shopping", "Shopping - Autres"): (MoneyMapType.CHOICE, "Shopping"),
        ("Shopping", "Autre"): (MoneyMapType.CHOICE, "Shopping"),
        ("Shopping", "Divers"): (MoneyMapType.CHOICE, "Shopping"),
        # Choice - Travel
        ("Voyages / Vacances", "Hôtels"): (MoneyMapType.CHOICE, "Travel and vacations"),
        ("Voyages / Vacances", "Billets d'avion"): (MoneyMapType.CHOICE, "Travel and vacations"),
        ("Voyages / Vacances", "Location vacances"): (MoneyMapType.CHOICE, "Travel and vacations"),
        # Compound - Savings
        ("Banque", "Epargne"): (MoneyMapType.COMPOUND, "Investments"),
        ("Banque", "Investissements"): (MoneyMapType.COMPOUND, "Investments"),
    }

    # ##>: Keywords indicating internal transfers (case-insensitive).
    INTERNAL_TRANSFER_KEYWORDS: ClassVar[list[str]] = [
        "virement interne",
        "vir interne",
        "transfert interne",
    ]

    @classmethod
    def get_deterministic_category(
        cls, bankin_category: str, bankin_subcategory: str
    ) -> tuple[MoneyMapType, str] | None:
        """
        Get Money Map category for a known Bankin' category pair.

        Parameters
        ----------
        bankin_category : str
            Bankin' main category.
        bankin_subcategory : str
            Bankin' subcategory.

        Returns
        -------
        tuple[MoneyMapType, str] | None
            Tuple of (MoneyMapType, subcategory) if mapping exists, None otherwise.
        """
        return cls.BANKIN_TO_MONEYMAP.get((bankin_category, bankin_subcategory))

    @classmethod
    def is_internal_transfer(cls, description: str) -> bool:
        """
        Check if a transaction description indicates an internal transfer.

        Parameters
        ----------
        description : str
            Transaction description text.

        Returns
        -------
        bool
            True if description contains internal transfer keywords.
        """
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in cls.INTERNAL_TRANSFER_KEYWORDS)
