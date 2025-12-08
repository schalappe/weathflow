"""Test data builders for CSV content using deterministic Bankin categories."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CSVTransaction:
    """Single transaction row for test CSV."""

    date: str
    description: str
    account: str
    amount: Decimal
    category: str
    subcategory: str


class CSVBuilder:
    """
    Build Bankin CSV content for integration tests.

    Uses deterministic Bankin categories from CategoryMapping to avoid Claude API calls.
    All methods are chainable for fluent test data creation.

    Examples
    --------
    >>> csv = CSVBuilder("2025-01").add_income("Salary", 3000).add_grocery("CARREFOUR", 150).build()
    >>> csv = CSVBuilder("2025-02").add_dining("Restaurant", 50).add_savings("Epargne", 500).build()
    """

    # ##>: Expected column format for BankinCSVParser.
    HEADER = "Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée"

    # ##>: Deterministic category pairs matching CategoryMapping.BANKIN_TO_MONEYMAP.
    CATEGORIES: dict[str, tuple[str, str]] = {
        "income": ("Entrées d'argent", "Salaires"),
        "grocery": ("Alimentation & Restau.", "Supermarché / Epicerie"),
        "dining": ("Alimentation & Restau.", "Fast foods"),
        "savings": ("Banque", "Epargne"),
        "transfer": ("Retraits, Chq. et Vir.", "Virements internes"),
        "transport": ("Transport", "Transports en commun"),
        "rent": ("Logement", "Loyer"),
        "utilities": ("Logement", "Charges"),
        "entertainment": ("Loisirs & Sorties", "Cinéma"),
    }

    def __init__(self, month: str = "2025-01") -> None:
        """
        Initialize builder for a specific month.

        Parameters
        ----------
        month : str
            Month in YYYY-MM format. Days auto-increment from 01.
        """
        self._month = month
        self._day = 1
        self._transactions: list[CSVTransaction] = []

    def _as_expense(self, amount: float) -> Decimal:
        """
        Convert positive amount to negative Decimal for expense transactions.

        Parameters
        ----------
        amount : float
            Positive amount value.

        Returns
        -------
        Decimal
            Negative decimal for expense.
        """
        return Decimal(str(-abs(amount)))

    def _as_income(self, amount: float) -> Decimal:
        """
        Convert amount to positive Decimal for income transactions.

        Parameters
        ----------
        amount : float
            Amount value.

        Returns
        -------
        Decimal
            Positive decimal for income.
        """
        return Decimal(str(abs(amount)))

    def add_income(self, description: str, amount: float) -> "CSVBuilder":
        """
        Add INCOME transaction (salary).

        Parameters
        ----------
        description : str
            Transaction description.
        amount : float
            Transaction amount (positive value).

        Returns
        -------
        CSVBuilder
            Self for method chaining.
        """
        cat, subcat = self.CATEGORIES["income"]
        self._add(description, self._as_income(amount), cat, subcat)
        return self

    def add_grocery(self, description: str, amount: float) -> "CSVBuilder":
        """
        Add CORE transaction (groceries).

        Parameters
        ----------
        description : str
            Transaction description.
        amount : float
            Transaction amount (will be converted to negative).

        Returns
        -------
        CSVBuilder
            Self for method chaining.
        """
        cat, subcat = self.CATEGORIES["grocery"]
        self._add(description, self._as_expense(amount), cat, subcat)
        return self

    def add_dining(self, description: str, amount: float) -> "CSVBuilder":
        """
        Add CHOICE transaction (dining out).

        Parameters
        ----------
        description : str
            Transaction description.
        amount : float
            Transaction amount (will be converted to negative).

        Returns
        -------
        CSVBuilder
            Self for method chaining.
        """
        cat, subcat = self.CATEGORIES["dining"]
        self._add(description, self._as_expense(amount), cat, subcat)
        return self

    def add_savings(self, description: str, amount: float) -> "CSVBuilder":
        """
        Add COMPOUND transaction (savings).

        Parameters
        ----------
        description : str
            Transaction description.
        amount : float
            Transaction amount (will be converted to negative).

        Returns
        -------
        CSVBuilder
            Self for method chaining.
        """
        cat, subcat = self.CATEGORIES["savings"]
        self._add(description, self._as_expense(amount), cat, subcat)
        return self

    def add_transfer(self, description: str, amount: float) -> "CSVBuilder":
        """
        Add EXCLUDED transaction (internal transfer).

        Parameters
        ----------
        description : str
            Transaction description.
        amount : float
            Transaction amount (will be converted to negative).

        Returns
        -------
        CSVBuilder
            Self for method chaining.
        """
        cat, subcat = self.CATEGORIES["transfer"]
        self._add(description, self._as_expense(amount), cat, subcat)
        return self

    def add_rent(self, description: str, amount: float) -> "CSVBuilder":
        """
        Add CORE transaction (rent).

        Parameters
        ----------
        description : str
            Transaction description.
        amount : float
            Transaction amount (will be converted to negative).

        Returns
        -------
        CSVBuilder
            Self for method chaining.
        """
        cat, subcat = self.CATEGORIES["rent"]
        self._add(description, self._as_expense(amount), cat, subcat)
        return self

    def add_entertainment(self, description: str, amount: float) -> "CSVBuilder":
        """
        Add CHOICE transaction (entertainment).

        Parameters
        ----------
        description : str
            Transaction description.
        amount : float
            Transaction amount (will be converted to negative).

        Returns
        -------
        CSVBuilder
            Self for method chaining.
        """
        cat, subcat = self.CATEGORIES["entertainment"]
        self._add(description, self._as_expense(amount), cat, subcat)
        return self

    def _add(self, description: str, amount: Decimal, category: str, subcategory: str) -> None:
        """Add a transaction with auto-incrementing date."""
        date = f"{self._day:02d}/{self._month[5:7]}/{self._month[:4]}"
        self._day += 1
        self._transactions.append(
            CSVTransaction(
                date=date,
                description=description,
                account="Main Account",
                amount=amount,
                category=category,
                subcategory=subcategory,
            )
        )

    def build(self) -> bytes:
        """
        Build CSV content as bytes ready for upload.

        Returns
        -------
        bytes
            UTF-8 encoded CSV content in Bankin format.
        """
        lines = [self.HEADER]
        for tx in self._transactions:
            # ##>: Format amount with comma decimal separator (French locale).
            amount_str = str(tx.amount).replace(".", ",")
            # ##>: Column order: Date;Description;Compte;Montant;Catégorie;Sous-Catégorie;Note;Pointée.
            lines.append(f"{tx.date};{tx.description};{tx.account};{amount_str};{tx.category};{tx.subcategory};;Non")
        return "\n".join(lines).encode("utf-8")


def combine_csvs(*csvs: bytes) -> bytes:
    """
    Combine multiple CSV byte strings, removing duplicate headers.

    Parameters
    ----------
    *csvs : bytes
        Variable number of CSV byte strings to combine.

    Returns
    -------
    bytes
        Combined CSV with single header.
    """
    if not csvs:
        return b""
    lines = csvs[0].decode("utf-8").split("\n")
    for csv in csvs[1:]:
        lines.extend(csv.decode("utf-8").split("\n")[1:])
    return "\n".join(lines).encode("utf-8")
