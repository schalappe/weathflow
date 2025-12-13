import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { TransactionEditModal } from "@/components/dashboard/transaction-edit-modal";
import { SUBCATEGORY_OPTIONS } from "@/lib/category-options";
import type { TransactionResponse, UpdateTransactionPayload } from "@/types";

// [>]: Factory function for mock transactions - keeps tests DRY.
const createMockTransaction = (
  overrides: Partial<TransactionResponse> = {},
): TransactionResponse => ({
  id: 1,
  date: "2025-10-15",
  description: "Grocery shopping",
  account: "Main Account",
  amount: -85.5,
  bankin_category: "Food",
  bankin_subcategory: "Groceries",
  money_map_type: "CORE",
  money_map_subcategory: "Groceries",
  is_manually_corrected: false,
  ...overrides,
});

// [>]: Default props factory - reduces boilerplate in each test.
const createDefaultProps = (
  overrides: Partial<Parameters<typeof TransactionEditModal>[0]> = {},
) => ({
  transaction: createMockTransaction(),
  isOpen: true,
  onClose: vi.fn(),
  onSave: vi.fn().mockResolvedValue(undefined),
  isSaving: false,
  error: null,
  ...overrides,
});

describe("TransactionEditModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders transaction details correctly", () => {
      const transaction = createMockTransaction({
        description: "Netflix Subscription",
        amount: -15.99,
        date: "2025-11-20",
      });
      render(<TransactionEditModal {...createDefaultProps({ transaction })} />);

      expect(screen.getByText("Netflix Subscription")).toBeInTheDocument();
      // [>]: Amount is formatted as currency with locale formatting.
      expect(screen.getByText(/-16[\s\u00A0]€/)).toBeInTheDocument();
      expect(screen.getByText("20/11")).toBeInTheDocument();
    });

    it("returns null when transaction is null", () => {
      const { container } = render(
        <TransactionEditModal {...createDefaultProps({ transaction: null })} />,
      );
      expect(container).toBeEmptyDOMElement();
    });

    it("displays error alert when error prop is set", () => {
      render(
        <TransactionEditModal
          {...createDefaultProps({ error: "Failed to save" })}
        />,
      );
      expect(screen.getByText("Failed to save")).toBeInTheDocument();
    });
  });

  describe("Type Change Updates Subcategory", () => {
    it("updates subcategory options when type changes from CORE to CHOICE", async () => {
      const user = userEvent.setup();
      render(<TransactionEditModal {...createDefaultProps()} />);

      // [>]: Open the type dropdown and select CHOICE (Plaisir).
      const typeSelect = screen.getByRole("combobox", {
        name: /Type de catégorie/i,
      });
      await user.click(typeSelect);
      await user.click(screen.getByRole("option", { name: "Plaisir" }));

      // [>]: Open subcategory dropdown and verify CHOICE options are present.
      const subcategorySelect = screen.getByRole("combobox", {
        name: /Sous-catégorie/i,
      });
      await user.click(subcategorySelect);

      // [>]: First CHOICE subcategory should be auto-selected and visible in options.
      expect(
        screen.getByRole("option", { name: "Restaurant" }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("option", { name: "Divertissement" }),
      ).toBeInTheDocument();
    });

    it("hides subcategory select when EXCLUDED type is selected", async () => {
      const user = userEvent.setup();
      render(<TransactionEditModal {...createDefaultProps()} />);

      const typeSelect = screen.getByRole("combobox", {
        name: /Type de catégorie/i,
      });
      await user.click(typeSelect);
      await user.click(screen.getByRole("option", { name: "Exclu" }));

      // [>]: EXCLUDED has no subcategories, so the select should not be present.
      expect(
        screen.queryByRole("combobox", { name: /Sous-catégorie/i }),
      ).not.toBeInTheDocument();
    });
  });

  describe("Save Button State", () => {
    it("disables save button when no changes made", () => {
      render(<TransactionEditModal {...createDefaultProps()} />);
      expect(
        screen.getByRole("button", { name: /Enregistrer/i }),
      ).toBeDisabled();
    });

    it("enables save button when type is changed", async () => {
      const user = userEvent.setup();
      render(<TransactionEditModal {...createDefaultProps()} />);

      const typeSelect = screen.getByRole("combobox", {
        name: /Type de catégorie/i,
      });
      await user.click(typeSelect);
      await user.click(screen.getByRole("option", { name: "Plaisir" }));

      expect(
        screen.getByRole("button", { name: /Enregistrer/i }),
      ).not.toBeDisabled();
    });

    it("enables save button when only subcategory is changed", async () => {
      const user = userEvent.setup();
      render(<TransactionEditModal {...createDefaultProps()} />);

      // [>]: Change only the subcategory within same type.
      const subcategorySelect = screen.getByRole("combobox", {
        name: /Sous-catégorie/i,
      });
      await user.click(subcategorySelect);

      // [>]: Select a different CORE subcategory (Housing → Logement).
      await user.click(screen.getByRole("option", { name: "Logement" }));

      expect(
        screen.getByRole("button", { name: /Enregistrer/i }),
      ).not.toBeDisabled();
    });

    it("disables save button when isSaving is true", async () => {
      const user = userEvent.setup();
      const { rerender } = render(
        <TransactionEditModal {...createDefaultProps()} />,
      );

      // [>]: Make a change first to enable the button.
      const typeSelect = screen.getByRole("combobox", {
        name: /Type de catégorie/i,
      });
      await user.click(typeSelect);
      await user.click(screen.getByRole("option", { name: "Plaisir" }));

      // [>]: Verify enabled before checking disabled state.
      expect(
        screen.getByRole("button", { name: /Enregistrer/i }),
      ).not.toBeDisabled();

      // [>]: Re-render with isSaving=true to test disabled state during save.
      rerender(
        <TransactionEditModal
          {...createDefaultProps({
            transaction: createMockTransaction({ money_map_type: "CHOICE" }),
            isSaving: true,
          })}
        />,
      );

      expect(
        screen.getByRole("button", { name: /Enregistrer/i }),
      ).toBeDisabled();
    });
  });

  describe("onSave Callback", () => {
    it("calls onSave with correct payload when saved", async () => {
      const user = userEvent.setup();
      const onSave = vi.fn().mockResolvedValue(undefined);
      render(<TransactionEditModal {...createDefaultProps({ onSave })} />);

      // [>]: Change type to COMPOUND (Épargne).
      const typeSelect = screen.getByRole("combobox", {
        name: /Type de catégorie/i,
      });
      await user.click(typeSelect);
      await user.click(screen.getByRole("option", { name: "Épargne" }));

      // [>]: First subcategory of COMPOUND is auto-selected: "Emergency Fund".
      await user.click(screen.getByRole("button", { name: /Enregistrer/i }));

      await waitFor(() => {
        expect(onSave).toHaveBeenCalledWith({
          money_map_type: "COMPOUND",
          money_map_subcategory: SUBCATEGORY_OPTIONS.COMPOUND[0],
        } satisfies UpdateTransactionPayload);
      });
    });

    it("passes null subcategory when EXCLUDED type is selected", async () => {
      const user = userEvent.setup();
      const onSave = vi.fn().mockResolvedValue(undefined);
      render(<TransactionEditModal {...createDefaultProps({ onSave })} />);

      const typeSelect = screen.getByRole("combobox", {
        name: /Type de catégorie/i,
      });
      await user.click(typeSelect);
      await user.click(screen.getByRole("option", { name: "Exclu" }));

      await user.click(screen.getByRole("button", { name: /Enregistrer/i }));

      await waitFor(() => {
        expect(onSave).toHaveBeenCalledWith({
          money_map_type: "EXCLUDED",
          money_map_subcategory: null,
        });
      });
    });
  });

  describe("Modal Interactions", () => {
    it("calls onClose when Cancel button is clicked", async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      render(<TransactionEditModal {...createDefaultProps({ onClose })} />);

      await user.click(screen.getByRole("button", { name: /Annuler/i }));

      expect(onClose).toHaveBeenCalledOnce();
    });
  });
});
