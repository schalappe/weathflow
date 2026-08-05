"use client";

/** @module advice-panel-content Monthly decision output loading and rendering. */

import Link from "next/link";
import { useCallback, useEffect, useReducer, useState } from "react";
import {
  AlertCircle,
  Calculator,
  CalendarDays,
  Database,
  Loader2,
  RefreshCw,
  Pencil,
  Scale,
  Sparkles,
  Upload,
  Trash2,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  deleteActivePriority,
  deleteCommitmentFact,
  deleteConstraintFact,
  deleteEmergencyFundFact,
  deleteIncomeFact,
  generateAdvice,
  getCommitmentContext,
  getConstraintContext,
  getEmergencyFundContext,
  getIncomeContext,
  getActivePriority,
  getAdvice,
  putActivePriority,
  putCommitmentFact,
  putConstraintFact,
  putEmergencyFundFact,
  putIncomeFact,
} from "@/lib/api-client";
import { t } from "@/lib/translations";
import {
  cn,
  formatAdviceTimestamp,
  formatCurrency,
  getErrorMessage,
} from "@/lib/utils";
import type {
  ActivePriority,
  ActivePriorityInput,
  AdviceData,
  CommitmentFact,
  CommitmentFactCitation,
  CommitmentFactInput,
  CommitmentFactType,
  CommitmentFrequency,
  ConstraintFact,
  ConstraintFactCitation,
  ConstraintFactInput,
  ConstraintFactType,
  EmergencyFundFact,
  EmergencyFundFactInput,
  EmergencyFundFactType,
  IncomeFact,
  IncomeFactCitation,
  IncomeFactInput,
  IncomeFactType,
  IncomeFrequency,
  ClarificationOutput,
  DecisionOutput,
  DecisionPriority,
  DeclaredFactCitation,
  DeclaredFactType,
  DecisionTrace,
  PeriodCoverageCitation,
  PeriodCoverageInput,
  EligibilityInfo,
  RecommendationOutput,
  TransactionNatureCitation,
  TransactionNatureInput,
} from "@/types";

type PanelState = "loading" | "loaded" | "empty" | "error";

interface AdviceState {
  panelState: PanelState;
  advice: AdviceData | null;
  generatedAt: string | null;
  isRegenerating: boolean;
  error: string | null;
  eligibility: EligibilityInfo | null;
}

type AdviceAction =
  | { type: "FETCH_START" }
  | {
      type: "FETCH_SUCCESS";
      advice: AdviceData;
      generatedAt: string;
      eligibility: EligibilityInfo;
    }
  | { type: "FETCH_EMPTY"; eligibility: EligibilityInfo }
  | { type: "FETCH_ERROR"; error: string }
  | { type: "REGENERATE_START" }
  | { type: "REGENERATE_SUCCESS"; advice: AdviceData; generatedAt: string }
  | { type: "REGENERATE_ERROR"; error: string };

const initialState: AdviceState = {
  panelState: "loading",
  advice: null,
  generatedAt: null,
  isRegenerating: false,
  error: null,
  eligibility: null,
};

const emergencyFundFactLabels: Record<EmergencyFundFactType, string> = {
  liquid_reserve: "Réserve liquide non affectée",
  safety_floor: "Plancher de sécurité",
  priority_allocation: "Montant déjà affecté à la priorité",
};

const emergencyFundInputLabels: Record<EmergencyFundFactType, string> = {
  liquid_reserve: "Montant de la réserve liquide non affectée",
  safety_floor: "Montant du plancher de sécurité",
  priority_allocation: "Montant déjà affecté à la priorité",
};

const commitmentFactLabels: Record<CommitmentFactType, string> = {
  recurring_obligation: "Obligation récurrente",
  one_off_obligation: "Obligation ponctuelle",
  debt_position: "Position de dette",
  debt_terms: "Conditions de dette",
};

const commitmentFactTypes: Record<CommitmentFactType, true> = {
  recurring_obligation: true,
  one_off_obligation: true,
  debt_position: true,
  debt_terms: true,
};

const incomeFactLabels: Record<IncomeFactType, string> = {
  usual_disposable_income: "Revenu disponible habituel",
  expected_one_off_income: "Entrée exceptionnelle attendue",
};

const incomeFrequencyLabels: Record<IncomeFrequency, string> = {
  weekly: "Hebdomadaire",
  biweekly: "Toutes les deux semaines",
  monthly: "Mensuelle",
  quarterly: "Trimestrielle",
  yearly: "Annuelle",
};

const clarificationFactLabels: Record<DeclaredFactType, string> = {
  period_coverage: "Couverture de la période",
  transaction_nature: "Nature de la transaction",
  active_priority: "Priorité active",
  ...emergencyFundFactLabels,
  ...commitmentFactLabels,
  ...incomeFactLabels,
  financial_limit: "Limite financière",
  action_unavailability: "Indisponibilité d’action",
};

const clarificationOutcomeLabels = {
  pending: "en attente",
  answered: "répondue",
  skipped: "passée",
  unknown: "inconnue",
} as const;

const clarificationStopLabels = {
  question_pending: "Une réponse peut encore changer le conseil.",
  no_remaining_decision_impact:
    "Arrêt : aucune réponse restante ne peut changer le conseil.",
  quota_reached: "Arrêt : plafond de trois questions atteint.",
} as const;

const contradictionSignalLabels: Record<
  NonNullable<ClarificationOutput["contradiction"]>["signal"],
  string
> = {
  recurring_income_lower: "Revenu récurrent inférieur",
  recurring_income_higher: "Revenu récurrent supérieur",
  recurring_obligation_higher: "Obligation récurrente supérieure",
  recurring_obligation_lower: "Obligation récurrente inférieure",
  one_off_income_mismatch: "Entrée exceptionnelle appariée différente",
  one_off_obligation_mismatch: "Obligation ponctuelle appariée différente",
};

const transactionNatureLabels: Record<
  TransactionNatureInput["nature"],
  string
> = {
  income: "Revenu",
  reimbursement: "Remboursement",
  transfer: "Transfert",
  expense: "Dépense",
  debt_payment: "Paiement de dette",
  saving: "Épargne",
};

const constraintFactTypes: Record<ConstraintFactType, true> = {
  financial_limit: true,
  action_unavailability: true,
};

function isPeriodCoverageFact(
  fact: DeclaredFactCitation,
): fact is PeriodCoverageCitation {
  return fact.fact_type === "period_coverage";
}

function isTransactionNatureFact(
  fact: DeclaredFactCitation,
): fact is TransactionNatureCitation {
  return fact.fact_type === "transaction_nature";
}

function isConstraintFactType(
  factType: string,
): factType is ConstraintFactType {
  return factType in constraintFactTypes;
}

function isConstraintFact(
  fact: DeclaredFactCitation,
): fact is ConstraintFactCitation {
  return isConstraintFactType(fact.fact_type);
}

function constraintInputFromForm(
  factType: ConstraintFactType,
  data: FormData,
): ConstraintFactInput {
  return factType === "financial_limit"
    ? {
        fact_type: factType,
        scope_type: String(data.get("scope_type")) as "expense" | "action",
        scope: String(data.get("scope")),
        limit_type: String(data.get("limit_type")) as
          | "floor"
          | "cap"
          | "sustainable_amount",
        amount: Number(data.get("amount")),
      }
    : {
        fact_type: factType,
        action: String(data.get("action")),
        review_date: String(data.get("review_date")),
      };
}

function constraintFactSummary(fact: ConstraintFactInput): string {
  return fact.fact_type === "financial_limit"
    ? `${fact.scope} — ${formatCurrency(fact.amount)}`
    : `${fact.action} — indisponible jusqu’au ${new Date(`${fact.review_date}T00:00:00`).toLocaleDateString("fr-FR")}`;
}

function isIncomeFactType(factType: string): factType is IncomeFactType {
  return (
    factType === "usual_disposable_income" ||
    factType === "expected_one_off_income"
  );
}

function isIncomeFact(fact: DeclaredFactCitation): fact is IncomeFactCitation {
  return isIncomeFactType(fact.fact_type);
}

function incomeInputFromForm(
  factType: IncomeFactType,
  data: FormData,
): IncomeFactInput {
  const amount = Number(data.get("amount"));
  const label = String(data.get("label"));
  return factType === "usual_disposable_income"
    ? {
        fact_type: factType,
        amount,
        frequency: String(data.get("frequency")) as IncomeFrequency,
      }
    : {
        fact_type: factType,
        ...(label ? { label } : {}),
        amount,
        expected_date: String(data.get("expected_date")),
      };
}

function incomeFactSummary(fact: IncomeFactInput): string {
  return fact.fact_type === "usual_disposable_income"
    ? `${incomeFactLabels[fact.fact_type]} — ${formatCurrency(fact.amount)} / ${incomeFrequencyLabels[fact.frequency].toLowerCase()}`
    : `${incomeFactLabels[fact.fact_type]}${fact.label ? ` (${fact.label})` : ""} — ${formatCurrency(fact.amount)} le ${new Date(`${fact.expected_date}T00:00:00`).toLocaleDateString("fr-FR")}`;
}

function isCommitmentFactType(
  factType: string,
): factType is CommitmentFactType {
  return factType in commitmentFactTypes;
}

function isCommitmentFact(
  fact: DeclaredFactCitation,
): fact is CommitmentFactCitation {
  return isCommitmentFactType(fact.fact_type);
}

function optionalNumber(value: FormDataEntryValue | null): number | null {
  return value == null || value === "" ? null : Number(value);
}

/**
 * Build typed commitment answer from native form values.
 * @param factType - Closed-catalog fact type.
 * @param data - Submitted fields.
 * @returns Valid API input shape.
 */
function commitmentInputFromForm(
  factType: CommitmentFactType,
  data: FormData,
): CommitmentFactInput {
  const label = String(data.get("label"));
  switch (factType) {
    case "recurring_obligation":
      return {
        fact_type: factType,
        label,
        amount: Number(data.get("amount")),
        frequency: String(data.get("frequency")) as CommitmentFrequency,
        end_date: String(data.get("end_date")) || null,
      };
    case "one_off_obligation":
      return {
        fact_type: factType,
        label,
        amount: Number(data.get("amount")),
        due_date: String(data.get("due_date")),
      };
    case "debt_position":
      return {
        fact_type: factType,
        label,
        balance: Number(data.get("balance")),
        overdue_amount: optionalNumber(data.get("overdue_amount")),
      };
    case "debt_terms":
      return {
        fact_type: factType,
        label,
        minimum_payment: Number(data.get("minimum_payment")),
        annual_rate: optionalNumber(data.get("annual_rate")),
        cost: optionalNumber(data.get("cost")),
        end_date: String(data.get("end_date")) || null,
      };
  }
}

function commitmentFactSummary(fact: CommitmentFactInput): string {
  switch (fact.fact_type) {
    case "recurring_obligation":
    case "one_off_obligation":
      return `${fact.label} — ${formatCurrency(fact.amount)}`;
    case "debt_position":
      return `${fact.label} — solde ${formatCurrency(fact.balance)}`;
    case "debt_terms":
      return `${fact.label} — minimum ${formatCurrency(fact.minimum_payment)}`;
  }
}

function adviceReducer(state: AdviceState, action: AdviceAction): AdviceState {
  switch (action.type) {
    case "FETCH_START":
      return { ...initialState };
    case "FETCH_SUCCESS":
      return {
        panelState: "loaded",
        advice: action.advice,
        generatedAt: action.generatedAt,
        isRegenerating: false,
        error: null,
        eligibility: action.eligibility,
      };
    case "FETCH_EMPTY":
      return {
        ...initialState,
        panelState: "empty",
        eligibility: action.eligibility,
      };
    case "FETCH_ERROR":
      return { ...initialState, panelState: "error", error: action.error };
    case "REGENERATE_START":
      return { ...state, isRegenerating: true, error: null };
    case "REGENERATE_SUCCESS":
      return {
        ...state,
        panelState: "loaded",
        advice: action.advice,
        generatedAt: action.generatedAt,
        isRegenerating: false,
      };
    case "REGENERATE_ERROR":
      return { ...state, isRegenerating: false, error: action.error };
  }
}

interface AdvicePanelContentProps {
  year: number;
  month: number;
  className?: string;
}

/**
 * Load and render monthly decision outputs.
 * @param props - Month and optional classes.
 * @returns Advice panel body.
 */
export function AdvicePanelContent({
  year,
  month,
  className,
}: AdvicePanelContentProps) {
  const [state, dispatch] = useReducer(adviceReducer, initialState);
  const [reloadKey, reload] = useReducer((value: number) => value + 1, 0);
  const [activePriority, setActivePriority] = useState<ActivePriority | null>(
    null,
  );
  const [emergencyFundFacts, setEmergencyFundFacts] = useState<
    EmergencyFundFact[]
  >([]);
  const [commitmentFacts, setCommitmentFacts] = useState<CommitmentFact[]>([]);
  const [incomeFacts, setIncomeFacts] = useState<IncomeFact[]>([]);
  const [constraintFacts, setConstraintFacts] = useState<ConstraintFact[]>([]);
  const [contextError, setContextError] = useState<string | null>(null);
  const canGenerate = state.eligibility?.can_generate ?? false;

  useEffect(() => {
    let active = true;
    dispatch({ type: "FETCH_START" });
    Promise.all([
      getActivePriority(),
      getEmergencyFundContext(),
      getCommitmentContext(),
      getIncomeContext(),
      getConstraintContext(),
    ])
      .then(
        ([
          { priority },
          emergencyFundContext,
          commitmentContext,
          incomeContext,
          constraintContext,
        ]) => {
          if (active) {
            setActivePriority(priority);
            setEmergencyFundFacts(emergencyFundContext.facts);
            setCommitmentFacts(commitmentContext.facts);
            setIncomeFacts(incomeContext.facts);
            setConstraintFacts(constraintContext.facts);
            setContextError(null);
          }
        },
      )
      .catch((error: unknown) => {
        if (active)
          setContextError(getErrorMessage(error, "Contexte indisponible."));
      });

    getAdvice(year, month)
      .then((response) => {
        if (!active) return;
        if (response.exists) {
          dispatch({
            type: "FETCH_SUCCESS",
            advice: response.advice,
            generatedAt: response.generated_at,
            eligibility: response.eligibility,
          });
        } else {
          dispatch({ type: "FETCH_EMPTY", eligibility: response.eligibility });
        }
      })
      .catch((error: unknown) => {
        if (!active) return;
        console.error("[AdvicePanelContent] Failed to load advice:", error);
        dispatch({
          type: "FETCH_ERROR",
          error: getErrorMessage(error, t.advice.loadError),
        });
      });

    return () => {
      active = false;
    };
  }, [year, month, reloadKey]);

  const handleGenerate = useCallback(async () => {
    const regenerate = state.panelState === "loaded";
    dispatch({ type: "REGENERATE_START" });
    try {
      const response = await generateAdvice(year, month, { regenerate });
      dispatch({
        type: "REGENERATE_SUCCESS",
        advice: response.advice,
        generatedAt: response.generated_at,
      });
    } catch (error) {
      console.error("[AdvicePanelContent] Failed to generate advice:", error);
      dispatch({
        type: "REGENERATE_ERROR",
        error: getErrorMessage(error, t.advice.generateError),
      });
    }
  }, [year, month, state.panelState]);

  const answerClarification = useCallback(
    async (
      options: NonNullable<Parameters<typeof generateAdvice>[2]>,
      refresh?: () => Promise<void>,
    ) => {
      dispatch({ type: "REGENERATE_START" });
      try {
        const response = await generateAdvice(year, month, {
          ...options,
          regenerate: true,
        });
        dispatch({
          type: "REGENERATE_SUCCESS",
          advice: response.advice,
          generatedAt: response.generated_at,
        });
        await refresh?.();
      } catch (error) {
        dispatch({
          type: "REGENERATE_ERROR",
          error: getErrorMessage(error, t.advice.generateError),
        });
      }
    },
    [year, month],
  );

  const handlePriorityAnswer = useCallback(
    (priority: ActivePriorityInput, rememberPriority: boolean) =>
      answerClarification(
        { activePriority: priority, rememberPriority },
        async () => setActivePriority((await getActivePriority()).priority),
      ),
    [answerClarification],
  );

  const handleEmergencyFundAnswer = useCallback(
    (fact: EmergencyFundFactInput, rememberFact: boolean) =>
      answerClarification({ emergencyFundFact: fact, rememberFact }, async () =>
        setEmergencyFundFacts((await getEmergencyFundContext()).facts),
      ),
    [answerClarification],
  );

  const handleCommitmentAnswer = useCallback(
    (fact: CommitmentFactInput, rememberFact: boolean) =>
      answerClarification({ commitmentFact: fact, rememberFact }, async () =>
        setCommitmentFacts((await getCommitmentContext()).facts),
      ),
    [answerClarification],
  );

  const handleIncomeAnswer = useCallback(
    (fact: IncomeFactInput, rememberFact: boolean) =>
      answerClarification({ incomeFact: fact, rememberFact }, async () =>
        setIncomeFacts((await getIncomeContext()).facts),
      ),
    [answerClarification],
  );

  const handleConstraintAnswer = useCallback(
    (fact: ConstraintFactInput, rememberFact: boolean) =>
      answerClarification({ constraintFact: fact, rememberFact }, async () =>
        setConstraintFacts((await getConstraintContext()).facts),
      ),
    [answerClarification],
  );

  const handlePeriodCoverageAnswer = useCallback(
    (coverage: PeriodCoverageInput) =>
      answerClarification({ periodCoverage: coverage }),
    [answerClarification],
  );

  const handleTransactionNatureAnswer = useCallback(
    (fact: TransactionNatureInput) =>
      answerClarification({ transactionNature: fact }),
    [answerClarification],
  );

  const handleClarificationAbstention = useCallback(
    (clarificationAction: "skip" | "unknown" | "delete") =>
      answerClarification({ clarificationAction }),
    [answerClarification],
  );

  const handlePriorityCorrection = useCallback(
    async (priority: ActivePriorityInput) => {
      try {
        setActivePriority((await putActivePriority(priority)).priority);
        reload();
      } catch (error) {
        setContextError(getErrorMessage(error, "Correction impossible."));
      }
    },
    [],
  );

  const handlePriorityDeletion = useCallback(async () => {
    if (!window.confirm("Supprimer cette priorité mémorisée ?")) return;
    try {
      await deleteActivePriority();
      setActivePriority(null);
      reload();
    } catch (error) {
      setContextError(getErrorMessage(error, "Suppression impossible."));
    }
  }, []);

  const handleEmergencyFundCorrection = useCallback(
    async (factType: EmergencyFundFactType, amount: number) => {
      try {
        const { fact } = await putEmergencyFundFact(factType, amount);
        setEmergencyFundFacts((facts) => [
          ...facts.filter((item) => item.fact_type !== factType),
          fact,
        ]);
        reload();
      } catch (error) {
        setContextError(getErrorMessage(error, "Correction impossible."));
      }
    },
    [],
  );

  const handleEmergencyFundDeletion = useCallback(
    async (factType: EmergencyFundFactType) => {
      if (!window.confirm("Supprimer ce fait mémorisé ?")) return;
      try {
        await deleteEmergencyFundFact(factType);
        setEmergencyFundFacts((facts) =>
          facts.filter((fact) => fact.fact_type !== factType),
        );
        reload();
      } catch (error) {
        setContextError(getErrorMessage(error, "Suppression impossible."));
      }
    },
    [],
  );

  const handleCommitmentCorrection = useCallback(
    async (factId: number, input: CommitmentFactInput) => {
      try {
        const { fact } = await putCommitmentFact(factId, input);
        setCommitmentFacts((facts) =>
          facts.map((item) => (item.fact_id === factId ? fact : item)),
        );
        reload();
      } catch (error) {
        setContextError(getErrorMessage(error, "Correction impossible."));
      }
    },
    [],
  );

  const handleCommitmentDeletion = useCallback(async (factId: number) => {
    if (!window.confirm("Supprimer cette obligation ou dette mémorisée ?"))
      return;
    try {
      await deleteCommitmentFact(factId);
      setCommitmentFacts((facts) =>
        facts.filter((fact) => fact.fact_id !== factId),
      );
      reload();
    } catch (error) {
      setContextError(getErrorMessage(error, "Suppression impossible."));
    }
  }, []);

  const handleIncomeCorrection = useCallback(async (input: IncomeFactInput) => {
    try {
      const { fact } = await putIncomeFact(input);
      setIncomeFacts((facts) => [
        ...facts.filter((item) => item.fact_type !== input.fact_type),
        fact,
      ]);
      reload();
    } catch (error) {
      setContextError(getErrorMessage(error, "Correction impossible."));
    }
  }, []);

  const handleIncomeDeletion = useCallback(async (factType: IncomeFactType) => {
    if (!window.confirm("Supprimer ce revenu mémorisé ?")) return;
    try {
      await deleteIncomeFact(factType);
      setIncomeFacts((facts) =>
        facts.filter((fact) => fact.fact_type !== factType),
      );
      reload();
    } catch (error) {
      setContextError(getErrorMessage(error, "Suppression impossible."));
    }
  }, []);

  const handleConstraintCorrection = useCallback(
    async (factId: number, input: ConstraintFactInput) => {
      try {
        const { fact } = await putConstraintFact(factId, input);
        setConstraintFacts((facts) =>
          facts.map((item) => (item.fact_id === factId ? fact : item)),
        );
        reload();
      } catch (error) {
        setContextError(getErrorMessage(error, "Correction impossible."));
      }
    },
    [],
  );

  const handleConstraintDeletion = useCallback(async (factId: number) => {
    if (
      !window.confirm("Supprimer cette limite ou indisponibilité mémorisée ?")
    )
      return;
    try {
      await deleteConstraintFact(factId);
      setConstraintFacts((facts) =>
        facts.filter((fact) => fact.fact_id !== factId),
      );
      reload();
    } catch (error) {
      setContextError(getErrorMessage(error, "Suppression impossible."));
    }
  }, []);

  return (
    <div className={cn("space-y-6", className)}>
      <ActivePriorityPanel
        priority={activePriority}
        error={contextError}
        onCorrect={handlePriorityCorrection}
        onDelete={handlePriorityDeletion}
      />
      <IncomeFactsPanel
        facts={incomeFacts}
        onCorrect={handleIncomeCorrection}
        onDelete={handleIncomeDeletion}
      />
      <EmergencyFundFactsPanel
        facts={emergencyFundFacts}
        onCorrect={handleEmergencyFundCorrection}
        onDelete={handleEmergencyFundDeletion}
      />
      <CommitmentFactsPanel
        facts={commitmentFacts}
        onCorrect={handleCommitmentCorrection}
        onDelete={handleCommitmentDeletion}
      />
      <ConstraintFactsPanel
        facts={constraintFacts}
        onCorrect={handleConstraintCorrection}
        onDelete={handleConstraintDeletion}
      />
      {state.panelState === "loading" && <AdviceSkeletonLoader />}
      {state.panelState === "empty" && (
        <EmptyState
          onGenerate={handleGenerate}
          isLoading={state.isRegenerating}
          canGenerate={canGenerate}
          error={state.error}
          eligibilityReason={state.eligibility?.reason ?? null}
        />
      )}
      {state.panelState === "error" && (
        <ErrorState error={state.error} onRetry={reload} />
      )}
      {state.panelState === "loaded" && state.advice && (
        <AdviceContent
          advice={state.advice}
          generatedAt={state.generatedAt}
          onRegenerate={handleGenerate}
          isRegenerating={state.isRegenerating}
          regenerateError={state.error}
          canRegenerate={canGenerate}
          onPriorityAnswer={handlePriorityAnswer}
          onEmergencyFundAnswer={handleEmergencyFundAnswer}
          onCommitmentAnswer={handleCommitmentAnswer}
          onIncomeAnswer={handleIncomeAnswer}
          onConstraintAnswer={handleConstraintAnswer}
          onPeriodCoverageAnswer={handlePeriodCoverageAnswer}
          onTransactionNatureAnswer={handleTransactionNatureAnswer}
          onClarificationAbstention={handleClarificationAbstention}
          onCorrectSession={reload}
        />
      )}
    </div>
  );
}

interface ActivePriorityPanelProps {
  priority: ActivePriority | null;
  error: string | null;
  onCorrect: (priority: ActivePriorityInput) => Promise<void>;
  onDelete: () => Promise<void>;
}

function ActivePriorityPanel({
  priority,
  error,
  onCorrect,
  onDelete,
}: ActivePriorityPanelProps) {
  const [editing, setEditing] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await onCorrect({
      goal: String(data.get("goal")),
      target: String(data.get("target")),
      deadline: String(data.get("deadline")) || null,
    });
    setEditing(false);
  }

  return (
    <section
      id="active-priority-context"
      className="space-y-4 rounded-xl border bg-muted/20 p-5"
      aria-labelledby="active-priority-title"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h4 id="active-priority-title" className="font-semibold">
          Contexte déclaré
        </h4>
        {priority && (
          <Badge
            variant={priority.state === "to_confirm" ? "secondary" : "outline"}
          >
            {priority.state === "active"
              ? "Actif"
              : priority.state === "corrected"
                ? "Corrigé"
                : "À confirmer"}
          </Badge>
        )}
      </div>
      {error && <ErrorAlert error={error} />}
      {!priority && (
        <p className="text-sm text-muted-foreground">
          Aucune priorité active mémorisée.
        </p>
      )}
      {priority && !editing && (
        <>
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">Objectif courant</dt>
              <dd className="font-medium">{priority.goal}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Cible</dt>
              <dd className="font-medium">{priority.target}</dd>
            </div>
            {priority.deadline && (
              <div>
                <dt className="text-muted-foreground">Échéance</dt>
                <dd>
                  {new Date(`${priority.deadline}T00:00:00`).toLocaleDateString(
                    "fr-FR",
                  )}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-muted-foreground">Dernière confirmation</dt>
              <dd>{formatAdviceTimestamp(priority.last_confirmed_at)}</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Valide jusqu’au</dt>
              <dd>
                {new Date(priority.valid_until).toLocaleDateString("fr-FR")}
              </dd>
            </div>
          </dl>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setEditing(true)}
            >
              <Pencil className="h-4 w-4" />
              Corriger
            </Button>
            <Button variant="destructive" size="sm" onClick={onDelete}>
              <Trash2 className="h-4 w-4" />
              Supprimer
            </Button>
          </div>
        </>
      )}
      {priority && editing && (
        <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="context-priority-goal">Objectif courant</Label>
            <Input
              id="context-priority-goal"
              name="goal"
              defaultValue={priority.goal}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="context-priority-target">Cible</Label>
            <Input
              id="context-priority-target"
              name="target"
              defaultValue={priority.target}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="context-priority-deadline">
              Échéance éventuelle
            </Label>
            <Input
              id="context-priority-deadline"
              name="deadline"
              type="date"
              defaultValue={priority.deadline ?? ""}
            />
          </div>
          <div className="flex items-end gap-2">
            <Button type="submit">Enregistrer</Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setEditing(false)}
            >
              Annuler
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}

interface IncomeFactsPanelProps {
  facts: IncomeFact[];
  onCorrect: (fact: IncomeFactInput) => Promise<void>;
  onDelete: (factType: IncomeFactType) => Promise<void>;
}

function IncomeFactsPanel({
  facts,
  onCorrect,
  onDelete,
}: IncomeFactsPanelProps) {
  return (
    <section className="space-y-4 rounded-xl border bg-muted/20 p-5">
      <h4 className="font-semibold">Revenus déclarés</h4>
      {facts.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Aucun revenu fiable mémorisé.
        </p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {facts.map((fact) => (
            <IncomeFactCard
              key={fact.fact_type}
              fact={fact}
              onCorrect={onCorrect}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function IncomeFactCard({
  fact,
  onCorrect,
  onDelete,
}: {
  fact: IncomeFact;
  onCorrect: (fact: IncomeFactInput) => Promise<void>;
  onDelete: (factType: IncomeFactType) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const label = incomeFactLabels[fact.fact_type];

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCorrect(
      incomeInputFromForm(fact.fact_type, new FormData(event.currentTarget)),
    );
    setEditing(false);
  }

  return (
    <article
      id={`income-context-${fact.fact_type}`}
      className="space-y-3 rounded-lg border bg-background/50 p-4"
    >
      <div className="flex items-start justify-between gap-2">
        <h5 className="text-sm font-medium">{incomeFactSummary(fact)}</h5>
        <Badge variant={fact.state === "to_confirm" ? "secondary" : "outline"}>
          {fact.state === "active"
            ? "Actif"
            : fact.state === "corrected"
              ? "Corrigé"
              : "À confirmer"}
        </Badge>
      </div>
      {editing ? (
        <form className="space-y-3" onSubmit={handleSubmit}>
          <IncomeFields
            factType={fact.fact_type}
            defaultValue={fact}
            idPrefix={`context-income-${fact.fact_type}`}
          />
          <div className="flex gap-2">
            <Button type="submit" size="sm">
              Enregistrer
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setEditing(false)}
            >
              Annuler
            </Button>
          </div>
        </form>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">
            Confirmé le {formatAdviceTimestamp(fact.last_confirmed_at)}
          </p>
          <p className="text-xs text-muted-foreground">
            Valide jusqu’au{" "}
            {new Date(fact.valid_until).toLocaleDateString("fr-FR")}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              aria-label={`Corriger ${label}`}
              onClick={() => setEditing(true)}
            >
              <Pencil className="h-4 w-4" />
              Corriger
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              aria-label={`Supprimer ${label}`}
              onClick={() => onDelete(fact.fact_type)}
            >
              <Trash2 className="h-4 w-4" />
              Supprimer
            </Button>
          </div>
        </>
      )}
    </article>
  );
}

function IncomeFields({
  factType,
  defaultValue,
  idPrefix,
}: {
  factType: IncomeFactType;
  defaultValue?: IncomeFactInput;
  idPrefix: string;
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <NumberField
        id={`${idPrefix}-amount`}
        name="amount"
        label={
          factType === "usual_disposable_income"
            ? "Montant du revenu disponible habituel"
            : "Montant de l’entrée exceptionnelle"
        }
        defaultValue={defaultValue?.amount}
        required
      />
      {factType === "usual_disposable_income" ? (
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-frequency`}>Fréquence</Label>
          <select
            id={`${idPrefix}-frequency`}
            name="frequency"
            defaultValue={
              defaultValue?.fact_type === "usual_disposable_income"
                ? defaultValue.frequency
                : "monthly"
            }
            className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
          >
            {Object.entries(incomeFrequencyLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <>
          <div className="space-y-2">
            <Label htmlFor={`${idPrefix}-label`}>Libellé attendu</Label>
            <Input
              id={`${idPrefix}-label`}
              name="label"
              defaultValue={
                defaultValue?.fact_type === "expected_one_off_income"
                  ? defaultValue.label
                  : undefined
              }
              placeholder="Ex. Prime annuelle"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor={`${idPrefix}-expected-date`}>Date attendue</Label>
            <Input
              id={`${idPrefix}-expected-date`}
              name="expected_date"
              type="date"
              defaultValue={
                defaultValue?.fact_type === "expected_one_off_income"
                  ? defaultValue.expected_date
                  : undefined
              }
              required
            />
          </div>
        </>
      )}
    </div>
  );
}

interface EmergencyFundFactsPanelProps {
  facts: EmergencyFundFact[];
  onCorrect: (factType: EmergencyFundFactType, amount: number) => Promise<void>;
  onDelete: (factType: EmergencyFundFactType) => Promise<void>;
}

function EmergencyFundFactsPanel({
  facts,
  onCorrect,
  onDelete,
}: EmergencyFundFactsPanelProps) {
  return (
    <section className="space-y-4 rounded-xl border bg-muted/20 p-5">
      <h4 className="font-semibold">Contexte du fonds d’urgence</h4>
      {facts.length === 0 ? (
        <p className="text-sm text-muted-foreground">Aucun montant mémorisé.</p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-3">
          {facts.map((fact) => (
            <EmergencyFundFactCard
              key={fact.fact_type}
              fact={fact}
              onCorrect={onCorrect}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function EmergencyFundFactCard({
  fact,
  onCorrect,
  onDelete,
}: {
  fact: EmergencyFundFact;
  onCorrect: (factType: EmergencyFundFactType, amount: number) => Promise<void>;
  onDelete: (factType: EmergencyFundFactType) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const label = emergencyFundFactLabels[fact.fact_type];

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    await onCorrect(fact.fact_type, Number(data.get("amount")));
    setEditing(false);
  }

  return (
    <article
      id={`emergency-fund-context-${fact.fact_type}`}
      className="space-y-3 rounded-lg border bg-background/50 p-4"
    >
      <div className="flex items-start justify-between gap-2">
        <h5 className="text-sm font-medium">{label}</h5>
        <Badge variant={fact.state === "to_confirm" ? "secondary" : "outline"}>
          {fact.state === "active"
            ? "Actif"
            : fact.state === "corrected"
              ? "Corrigé"
              : "À confirmer"}
        </Badge>
      </div>
      {editing ? (
        <form className="space-y-3" onSubmit={handleSubmit}>
          <Label htmlFor={`context-${fact.fact_type}-amount`}>
            Montant en euros
          </Label>
          <Input
            id={`context-${fact.fact_type}-amount`}
            name="amount"
            type="number"
            min="0"
            step="0.01"
            defaultValue={fact.amount}
            required
          />
          <div className="flex gap-2">
            <Button type="submit" size="sm">
              Enregistrer
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setEditing(false)}
            >
              Annuler
            </Button>
          </div>
        </form>
      ) : (
        <>
          <p className="text-lg font-semibold">{formatCurrency(fact.amount)}</p>
          <p className="text-xs text-muted-foreground">
            Confirmé le {formatAdviceTimestamp(fact.last_confirmed_at)}
          </p>
          <p className="text-xs text-muted-foreground">
            Valide jusqu’au{" "}
            {new Date(fact.valid_until).toLocaleDateString("fr-FR")}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              aria-label={`Corriger ${label}`}
              onClick={() => setEditing(true)}
            >
              <Pencil className="h-4 w-4" />
              Corriger
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              aria-label={`Supprimer ${label}`}
              onClick={() => onDelete(fact.fact_type)}
            >
              <Trash2 className="h-4 w-4" />
              Supprimer
            </Button>
          </div>
        </>
      )}
    </article>
  );
}

interface CommitmentFactsPanelProps {
  facts: CommitmentFact[];
  onCorrect: (factId: number, fact: CommitmentFactInput) => Promise<void>;
  onDelete: (factId: number) => Promise<void>;
}

function CommitmentFactsPanel({
  facts,
  onCorrect,
  onDelete,
}: CommitmentFactsPanelProps) {
  return (
    <section className="space-y-4 rounded-xl border bg-muted/20 p-5">
      <h4 className="font-semibold">Obligations et dettes déclarées</h4>
      {facts.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Aucune obligation ou dette mémorisée.
        </p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {facts.map((fact) => (
            <CommitmentFactCard
              key={fact.fact_id}
              fact={fact}
              onCorrect={onCorrect}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function CommitmentFactCard({
  fact,
  onCorrect,
  onDelete,
}: {
  fact: CommitmentFact;
  onCorrect: (factId: number, fact: CommitmentFactInput) => Promise<void>;
  onDelete: (factId: number) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCorrect(
      fact.fact_id,
      commitmentInputFromForm(
        fact.fact_type,
        new FormData(event.currentTarget),
      ),
    );
    setEditing(false);
  }

  return (
    <article
      id={`commitment-context-${fact.fact_id}`}
      className="space-y-3 rounded-lg border bg-background/50 p-4"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h5 className="text-sm font-medium">
            {commitmentFactLabels[fact.fact_type]}
          </h5>
          <p>{commitmentFactSummary(fact)}</p>
        </div>
        <Badge variant={fact.state === "to_confirm" ? "secondary" : "outline"}>
          {fact.state === "active"
            ? "Actif"
            : fact.state === "corrected"
              ? "Corrigé"
              : "À confirmer"}
        </Badge>
      </div>
      {editing ? (
        <form className="space-y-3" onSubmit={handleSubmit}>
          <CommitmentFields
            factType={fact.fact_type}
            defaultValue={fact}
            idPrefix={`context-commitment-${fact.fact_id}`}
          />
          <div className="flex gap-2">
            <Button type="submit" size="sm">
              Enregistrer
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setEditing(false)}
            >
              Annuler
            </Button>
          </div>
        </form>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">
            Confirmé le {formatAdviceTimestamp(fact.last_confirmed_at)}
          </p>
          <p className="text-xs text-muted-foreground">
            Valide jusqu’au{" "}
            {new Date(fact.valid_until).toLocaleDateString("fr-FR")}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setEditing(true)}
            >
              <Pencil className="h-4 w-4" />
              Corriger
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              onClick={() => onDelete(fact.fact_id)}
            >
              <Trash2 className="h-4 w-4" />
              Supprimer
            </Button>
          </div>
        </>
      )}
    </article>
  );
}

function CommitmentFields({
  factType,
  defaultValue,
  idPrefix,
}: {
  factType: CommitmentFactType;
  defaultValue?: CommitmentFactInput;
  idPrefix: string;
}) {
  const amount =
    defaultValue?.fact_type === "recurring_obligation" ||
    defaultValue?.fact_type === "one_off_obligation"
      ? defaultValue.amount
      : undefined;
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-label`}>Libellé</Label>
        <Input
          id={`${idPrefix}-label`}
          name="label"
          defaultValue={defaultValue?.label}
          required
        />
      </div>
      {(factType === "recurring_obligation" ||
        factType === "one_off_obligation") && (
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-amount`}>Montant</Label>
          <Input
            id={`${idPrefix}-amount`}
            name="amount"
            type="number"
            min="0.01"
            step="0.01"
            defaultValue={amount}
            required
          />
        </div>
      )}
      {factType === "recurring_obligation" && (
        <>
          <div className="space-y-2">
            <Label htmlFor={`${idPrefix}-frequency`}>Fréquence</Label>
            <select
              id={`${idPrefix}-frequency`}
              name="frequency"
              defaultValue={
                defaultValue?.fact_type === "recurring_obligation"
                  ? defaultValue.frequency
                  : "monthly"
              }
              className="h-9 w-full rounded-md border bg-transparent px-3 text-sm"
            >
              <option value="weekly">Hebdomadaire</option>
              <option value="biweekly">Toutes les deux semaines</option>
              <option value="monthly">Mensuelle</option>
              <option value="quarterly">Trimestrielle</option>
              <option value="yearly">Annuelle</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor={`${idPrefix}-end-date`}>
              Date de fin éventuelle
            </Label>
            <Input
              id={`${idPrefix}-end-date`}
              name="end_date"
              type="date"
              defaultValue={
                defaultValue?.fact_type === "recurring_obligation"
                  ? (defaultValue.end_date ?? "")
                  : ""
              }
            />
          </div>
        </>
      )}
      {factType === "one_off_obligation" && (
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-due-date`}>Échéance</Label>
          <Input
            id={`${idPrefix}-due-date`}
            name="due_date"
            type="date"
            defaultValue={
              defaultValue?.fact_type === "one_off_obligation"
                ? defaultValue.due_date
                : ""
            }
            required
          />
        </div>
      )}
      {factType === "debt_position" && (
        <>
          <NumberField
            id={`${idPrefix}-balance`}
            name="balance"
            label="Solde"
            defaultValue={
              defaultValue?.fact_type === "debt_position"
                ? defaultValue.balance
                : undefined
            }
            required
          />
          <NumberField
            id={`${idPrefix}-overdue`}
            name="overdue_amount"
            label="Montant en retard éventuel"
            defaultValue={
              defaultValue?.fact_type === "debt_position"
                ? (defaultValue.overdue_amount ?? undefined)
                : undefined
            }
          />
        </>
      )}
      {factType === "debt_terms" && (
        <>
          <NumberField
            id={`${idPrefix}-minimum`}
            name="minimum_payment"
            label="Paiement minimum"
            defaultValue={
              defaultValue?.fact_type === "debt_terms"
                ? defaultValue.minimum_payment
                : undefined
            }
            required
          />
          <NumberField
            id={`${idPrefix}-rate`}
            name="annual_rate"
            label="Taux annuel (%)"
            defaultValue={
              defaultValue?.fact_type === "debt_terms"
                ? (defaultValue.annual_rate ?? undefined)
                : undefined
            }
          />
          <NumberField
            id={`${idPrefix}-cost`}
            name="cost"
            label="Coût éventuel"
            defaultValue={
              defaultValue?.fact_type === "debt_terms"
                ? (defaultValue.cost ?? undefined)
                : undefined
            }
          />
          <div className="space-y-2">
            <Label htmlFor={`${idPrefix}-end-date`}>
              Date de fin éventuelle
            </Label>
            <Input
              id={`${idPrefix}-end-date`}
              name="end_date"
              type="date"
              defaultValue={
                defaultValue?.fact_type === "debt_terms"
                  ? (defaultValue.end_date ?? "")
                  : ""
              }
            />
          </div>
        </>
      )}
    </div>
  );
}

function ConstraintFactsPanel({
  facts,
  onCorrect,
  onDelete,
}: {
  facts: ConstraintFact[];
  onCorrect: (factId: number, fact: ConstraintFactInput) => Promise<void>;
  onDelete: (factId: number) => Promise<void>;
}) {
  return (
    <section className="space-y-4 rounded-xl border bg-muted/20 p-5">
      <h4 className="font-semibold">Limites et indisponibilités</h4>
      {facts.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Aucune contrainte financière mémorisée.
        </p>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {facts.map((fact) => (
            <ConstraintFactCard
              key={fact.fact_id}
              fact={fact}
              onCorrect={onCorrect}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function ConstraintFactCard({
  fact,
  onCorrect,
  onDelete,
}: {
  fact: ConstraintFact;
  onCorrect: (factId: number, fact: ConstraintFactInput) => Promise<void>;
  onDelete: (factId: number) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const label = fact.fact_type === "financial_limit" ? fact.scope : fact.action;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCorrect(
      fact.fact_id,
      constraintInputFromForm(
        fact.fact_type,
        new FormData(event.currentTarget),
      ),
    );
    setEditing(false);
  }

  return (
    <article
      id={`constraint-context-${fact.fact_id}`}
      className="space-y-3 rounded-lg border bg-background/50 p-4"
    >
      <div className="flex items-start justify-between gap-2">
        <h5 className="text-sm font-medium">{constraintFactSummary(fact)}</h5>
        <Badge variant={fact.state === "to_confirm" ? "secondary" : "outline"}>
          {fact.state === "active"
            ? "Actif"
            : fact.state === "corrected"
              ? "Corrigé"
              : "À confirmer"}
        </Badge>
      </div>
      {editing ? (
        <form className="space-y-3" onSubmit={handleSubmit}>
          <ConstraintFields
            factType={fact.fact_type}
            defaultValue={fact}
            idPrefix={`context-constraint-${fact.fact_id}`}
          />
          <div className="flex gap-2">
            <Button type="submit" size="sm">
              Enregistrer
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setEditing(false)}
            >
              Annuler
            </Button>
          </div>
        </form>
      ) : (
        <>
          <p className="text-xs text-muted-foreground">
            Confirmé le {formatAdviceTimestamp(fact.last_confirmed_at)}
          </p>
          <p className="text-xs text-muted-foreground">
            Valide jusqu’au{" "}
            {new Date(fact.valid_until).toLocaleDateString("fr-FR")}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              aria-label={`Corriger ${label}`}
              onClick={() => setEditing(true)}
            >
              <Pencil className="h-4 w-4" />
              Corriger
            </Button>
            <Button
              type="button"
              variant="destructive"
              size="sm"
              aria-label={`Supprimer ${label}`}
              onClick={() => onDelete(fact.fact_id)}
            >
              <Trash2 className="h-4 w-4" />
              Supprimer
            </Button>
          </div>
        </>
      )}
    </article>
  );
}

function ConstraintFields({
  factType,
  defaultValue,
  idPrefix,
}: {
  factType: ConstraintFactType;
  defaultValue?: ConstraintFactInput;
  idPrefix: string;
}) {
  if (factType === "action_unavailability") {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-action`}>Action indisponible</Label>
          <Input
            id={`${idPrefix}-action`}
            name="action"
            defaultValue={
              defaultValue?.fact_type === "action_unavailability"
                ? defaultValue.action
                : ""
            }
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-review-date`}>Date de réexamen</Label>
          <Input
            id={`${idPrefix}-review-date`}
            name="review_date"
            type="date"
            defaultValue={
              defaultValue?.fact_type === "action_unavailability"
                ? defaultValue.review_date
                : ""
            }
            required
          />
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-scope-type`}>Type de portée</Label>
        <select
          id={`${idPrefix}-scope-type`}
          name="scope_type"
          defaultValue={
            defaultValue?.fact_type === "financial_limit"
              ? defaultValue.scope_type
              : "expense"
          }
          className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
        >
          <option value="expense">Poste</option>
          <option value="action">Action</option>
        </select>
      </div>
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-scope`}>Portée exacte</Label>
        <Input
          id={`${idPrefix}-scope`}
          name="scope"
          defaultValue={
            defaultValue?.fact_type === "financial_limit"
              ? defaultValue.scope
              : ""
          }
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-limit-type`}>Type de limite</Label>
        <select
          id={`${idPrefix}-limit-type`}
          name="limit_type"
          defaultValue={
            defaultValue?.fact_type === "financial_limit"
              ? defaultValue.limit_type
              : "sustainable_amount"
          }
          className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
        >
          <option value="floor">Plancher</option>
          <option value="cap">Plafond</option>
          <option value="sustainable_amount">Montant soutenable</option>
        </select>
      </div>
      <NumberField
        id={`${idPrefix}-amount`}
        name="amount"
        label="Montant en euros"
        defaultValue={
          defaultValue?.fact_type === "financial_limit"
            ? defaultValue.amount
            : undefined
        }
        required
      />
    </div>
  );
}
function NumberField({
  id,
  name,
  label,
  defaultValue,
  required = false,
}: {
  id: string;
  name: string;
  label: string;
  defaultValue?: number;
  required?: boolean;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        name={name}
        type="number"
        min="0"
        step="0.01"
        defaultValue={defaultValue}
        required={required}
      />
    </div>
  );
}
function AdviceSkeletonLoader() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-6 w-40" />
      <Skeleton className="h-32 w-full rounded-xl" />
      <Skeleton className="h-32 w-full rounded-xl" />
    </div>
  );
}

interface EmptyStateProps {
  onGenerate: () => void;
  isLoading: boolean;
  canGenerate: boolean;
  error: string | null;
  eligibilityReason: string | null;
}

function EmptyState({
  onGenerate,
  isLoading,
  canGenerate,
  error,
  eligibilityReason,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-6 py-10 text-center">
      {error && <ErrorAlert error={error} />}
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-500/10">
        <Sparkles className="h-8 w-8 text-violet-600 dark:text-violet-400" />
      </div>
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">
          {canGenerate ? t.advice.empty.title : t.advice.notAvailable.title}
        </h3>
        <p className="mx-auto max-w-sm text-muted-foreground">
          {canGenerate
            ? t.advice.empty.description
            : eligibilityReason || t.advice.notAvailable.description}
        </p>
      </div>
      {canGenerate && (
        <Button onClick={onGenerate} disabled={isLoading} className="gap-2">
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {t.advice.generating}
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              {t.advice.empty.button}
            </>
          )}
        </Button>
      )}
    </div>
  );
}

function isDataRelatedError(error: string | null): boolean {
  if (!error) return false;
  const value = error.toLowerCase();
  return ["mois", "month", "donnees", "data", "not found", "insufficient"].some(
    (term) => value.includes(term),
  );
}

function ErrorState({
  error,
  onRetry,
}: {
  error: string | null;
  onRetry: () => void;
}) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span>{error}</span>
        {isDataRelatedError(error) ? (
          <Button variant="outline" size="sm" asChild>
            <Link href="/import">
              <Upload className="h-4 w-4" />
              {t.advice.importData}
            </Link>
          </Button>
        ) : (
          <Button variant="outline" size="sm" onClick={onRetry}>
            <RefreshCw className="h-4 w-4" />
            {t.advice.retry}
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

function ErrorAlert({ error }: { error: string }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>{error}</AlertDescription>
    </Alert>
  );
}

const outputLabels: Record<DecisionOutput["type"], string> = {
  recommendation: t.advice.outputTypes.recommendation,
  no_action: t.advice.outputTypes.noAction,
  unresolved: t.advice.outputTypes.unresolved,
  clarification: "Clarification",
};

const uncertaintyLabels = {
  supported: "Étayé",
  robust_despite_limit: "Robuste malgré une limite explicite",
  unresolved: "Sujet non conclu",
} as const;

const priorityLabels: Record<DecisionPriority, string> = {
  high: t.advice.priorities.high,
  medium: t.advice.priorities.medium,
  low: t.advice.priorities.low,
};

function RecommendationMetadata({ output }: { output: RecommendationOutput }) {
  if (output.amount == null && output.deadline == null) return null;

  return (
    <dl className="flex flex-wrap gap-4 text-sm">
      {output.amount != null && (
        <div className="rounded-lg bg-emerald-500/10 px-3 py-2">
          <dt className="text-muted-foreground">{t.advice.amount}</dt>
          <dd className="font-semibold text-emerald-700 dark:text-emerald-400">
            {formatCurrency(output.amount)}
          </dd>
        </div>
      )}
      {output.deadline != null && (
        <div className="rounded-lg bg-blue-500/10 px-3 py-2">
          <dt className="text-muted-foreground">{t.advice.deadline}</dt>
          <dd className="font-semibold text-blue-700 dark:text-blue-400">
            {new Date(`${output.deadline}T00:00:00`).toLocaleDateString(
              "fr-FR",
            )}
          </dd>
        </div>
      )}
    </dl>
  );
}

function TraceList({
  title,
  items,
  icon,
}: {
  title: string;
  items: string[];
  icon: React.ReactNode;
}) {
  if (items.length === 0) return null;
  return (
    <section className="space-y-2">
      <h6 className="flex items-center gap-2 text-sm font-medium">
        {icon}
        {title}
      </h6>
      <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
        {items.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function DecisionTraceDetails({
  trace,
  onCorrectSession,
}: {
  trace: DecisionTrace;
  onCorrectSession: () => void;
}) {
  return (
    <details className="group rounded-lg border bg-background/50 p-4">
      <summary className="cursor-pointer font-medium">
        {t.advice.traceDetails}
      </summary>
      <div className="mt-4 space-y-4">
        <section className="space-y-2">
          <h6 className="flex items-center gap-2 text-sm font-medium">
            <Database className="h-4 w-4" />
            {t.advice.observedFacts}
          </h6>
          <ul className="space-y-3">
            {trace.details.observations.map((observation, index) => (
              <li key={index} className="rounded-lg bg-muted/50 p-3 text-sm">
                <p>{observation.fact}</p>
                <p className="mt-1 text-muted-foreground">
                  {observation.period}
                </p>
                <p className="text-muted-foreground">{observation.scope}</p>
                <Link
                  href={`/?month=${observation.source_months[observation.source_months.length - 1]}${
                    observation.transaction_ids[0]
                      ? `&transaction=${observation.transaction_ids[0]}`
                      : ""
                  }`}
                  className="mt-2 inline-block font-medium text-primary underline-offset-4 hover:underline"
                >
                  Voir les transactions
                </Link>
              </li>
            ))}
          </ul>
        </section>
        {trace.details.declared_facts.length > 0 && (
          <section className="space-y-2">
            <h6 className="flex items-center gap-2 text-sm font-medium">
              <Sparkles className="h-4 w-4" />
              Faits déclarés
            </h6>
            <ul className="space-y-3">
              {trace.details.declared_facts.map((fact) => (
                <li
                  key={`${fact.fact_type}-${fact.last_confirmed_at}`}
                  className="space-y-1 rounded-lg bg-muted/50 p-3 text-sm"
                >
                  {fact.fact_type === "active_priority" ? (
                    <>
                      <p className="font-medium">
                        {fact.goal} — {fact.target}
                      </p>
                      {fact.deadline && (
                        <p className="text-muted-foreground">
                          Échéance :{" "}
                          {new Date(
                            `${fact.deadline}T00:00:00`,
                          ).toLocaleDateString("fr-FR")}
                        </p>
                      )}
                    </>
                  ) : isPeriodCoverageFact(fact) ? (
                    <p className="font-medium">
                      Couverture {fact.complete ? "complète" : "incomplète"} —{" "}
                      {fact.coverage_months.join(", ")}
                    </p>
                  ) : isTransactionNatureFact(fact) ? (
                    <p className="font-medium">
                      {transactionNatureLabels[fact.nature]} — transaction
                      {fact.transaction_ids.length > 1 ? "s" : ""}{" "}
                      {fact.transaction_ids.join(", ")}
                    </p>
                  ) : isIncomeFact(fact) ? (
                    <>
                      <p className="font-medium">{incomeFactSummary(fact)}</p>
                      {fact.matched_transaction && (
                        <p className="text-muted-foreground">
                          Déjà rapprochée d’une opération observée ; comptée une
                          seule fois.
                        </p>
                      )}
                    </>
                  ) : isCommitmentFact(fact) ? (
                    <p className="font-medium">{commitmentFactSummary(fact)}</p>
                  ) : isConstraintFact(fact) ? (
                    <p className="font-medium">{constraintFactSummary(fact)}</p>
                  ) : (
                    <p className="font-medium">
                      {emergencyFundFactLabels[fact.fact_type]} —{" "}
                      {formatCurrency(fact.amount)}
                    </p>
                  )}
                  <p className="text-muted-foreground">
                    Statut :{" "}
                    {fact.state === "session" ? "Cette session" : fact.state}
                  </p>
                  <p className="text-muted-foreground">
                    Confirmé le {formatAdviceTimestamp(fact.last_confirmed_at)}
                  </p>
                  <p className="text-muted-foreground">
                    {isPeriodCoverageFact(fact) || isTransactionNatureFact(fact)
                      ? "Portée limitée aux éléments confirmés"
                      : fact.valid_until
                        ? `Valide jusqu’au ${new Date(fact.valid_until).toLocaleDateString("fr-FR")}`
                        : "Valide pour cette session"}
                  </p>
                  {fact.state === "session" ? (
                    <div className="flex flex-wrap gap-2 pt-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        aria-label="Corriger cette réponse de session"
                        onClick={onCorrectSession}
                      >
                        Corriger
                      </Button>
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        aria-label="Supprimer cette réponse de session"
                        onClick={onCorrectSession}
                      >
                        Supprimer
                      </Button>
                    </div>
                  ) : (
                    <a
                      href={
                        isTransactionNatureFact(fact)
                          ? `/?month=${fact.source_months[fact.source_months.length - 1]}&transaction=${fact.transaction_ids[0]}`
                          : isPeriodCoverageFact(fact)
                            ? "/import"
                            : fact.fact_type === "active_priority"
                              ? "#active-priority-context"
                              : isIncomeFact(fact)
                                ? `#income-context-${fact.fact_type}`
                                : isCommitmentFact(fact)
                                  ? `#commitment-context-${fact.fact_id}`
                                  : isConstraintFact(fact)
                                    ? `#constraint-context-${fact.fact_id}`
                                    : `#emergency-fund-context-${fact.fact_type}`
                      }
                      className="inline-block font-medium text-primary underline-offset-4 hover:underline"
                    >
                      Corriger ou supprimer
                    </a>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}
        <TraceList
          title={t.advice.calculations}
          items={trace.details.calculations}
          icon={<Calculator className="h-4 w-4" />}
        />
        <TraceList
          title="Normalisation des revenus"
          items={trace.details.income_normalizations.map(
            (income) =>
              `${formatCurrency(income.source_amount)}${income.source_frequency ? ` / ${incomeFrequencyLabels[income.source_frequency].toLowerCase()}` : ""} → ${formatCurrency(income.normalized_amount)} · ${income.period} · ${income.conversion}`,
          )}
          icon={<Calculator className="h-4 w-4" />}
        />
        <TraceList
          title={t.advice.conventions}
          items={trace.details.conventions}
          icon={<Scale className="h-4 w-4" />}
        />
        <TraceList
          title="Transitions"
          items={trace.details.transitions ?? []}
          icon={<RefreshCw className="h-4 w-4" />}
        />
        <TraceList
          title={t.advice.limits}
          items={trace.details.limits}
          icon={<AlertCircle className="h-4 w-4" />}
        />
      </div>
    </details>
  );
}

type DecidedOutput = Exclude<DecisionOutput, ClarificationOutput>;

interface ClarificationCardProps {
  output: ClarificationOutput;
  isSubmitting: boolean;
  onPriorityAnswer: (
    priority: ActivePriorityInput,
    rememberPriority: boolean,
  ) => Promise<void>;
  onEmergencyFundAnswer: (
    fact: EmergencyFundFactInput,
    rememberFact: boolean,
  ) => Promise<void>;
  onCommitmentAnswer: (
    fact: CommitmentFactInput,
    rememberFact: boolean,
  ) => Promise<void>;
  onIncomeAnswer: (
    fact: IncomeFactInput,
    rememberFact: boolean,
  ) => Promise<void>;
  onConstraintAnswer: (
    fact: ConstraintFactInput,
    rememberFact: boolean,
  ) => Promise<void>;
  onPeriodCoverageAnswer: (coverage: PeriodCoverageInput) => Promise<void>;
  onTransactionNatureAnswer: (fact: TransactionNatureInput) => Promise<void>;
  onAbstain: (action: "skip" | "unknown" | "delete") => Promise<void>;
}

function ClarificationCard({
  output,
  isSubmitting,
  onPriorityAnswer,
  onEmergencyFundAnswer,
  onCommitmentAnswer,
  onIncomeAnswer,
  onConstraintAnswer,
  onPeriodCoverageAnswer,
  onTransactionNatureAnswer,
  onAbstain,
}: ClarificationCardProps) {
  const [coverageComplete, setCoverageComplete] = useState(true);
  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const submitter = (event.nativeEvent as SubmitEvent)
      .submitter as HTMLButtonElement | null;
    const remember = submitter?.value === "true";
    if (output.contradiction) {
      const resolution = submitter?.value;
      const amount =
        resolution === "confirm"
          ? output.contradiction.declared_value
          : Number(data.get("amount"));
      const rememberResolution = resolution !== "session";
      if (output.fact_type === "usual_disposable_income") {
        await onIncomeAnswer(
          {
            fact_type: output.fact_type,
            amount,
            frequency: output.contradiction.frequency!,
          },
          rememberResolution,
        );
      } else if (output.fact_type === "recurring_obligation") {
        await onCommitmentAnswer(
          {
            fact_type: output.fact_type,
            label: output.contradiction.label ?? output.subject,
            amount,
            frequency: output.contradiction.frequency!,
            end_date: null,
          },
          rememberResolution,
        );
      } else if (output.fact_type === "expected_one_off_income") {
        await onIncomeAnswer(
          {
            fact_type: output.fact_type,
            ...(output.contradiction.label
              ? { label: output.contradiction.label }
              : {}),
            amount,
            expected_date: output.contradiction.event_date!,
          },
          rememberResolution,
        );
      } else if (output.fact_type === "one_off_obligation") {
        await onCommitmentAnswer(
          {
            fact_type: output.fact_type,
            label: output.contradiction.label ?? output.subject,
            amount,
            due_date: output.contradiction.event_date!,
          },
          rememberResolution,
        );
      }
      return;
    }
    if (output.fact_type === "period_coverage") {
      const complete = data.get("complete") === "true";
      await onPeriodCoverageAnswer({
        coverage_months: output.coverage_months ?? [],
        complete,
        missing_elements: complete
          ? []
          : String(data.get("missing_elements"))
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean),
      });
      return;
    }
    if (output.fact_type === "transaction_nature") {
      const scope = String(
        data.get("scope"),
      ) as TransactionNatureInput["scope"];
      const transactionIds = output.transaction_ids ?? [];
      await onTransactionNatureAnswer({
        transaction_ids:
          scope === "occurrence" ? transactionIds.slice(0, 1) : transactionIds,
        nature: String(data.get("nature")) as TransactionNatureInput["nature"],
        scope,
      });
      return;
    }
    if (output.fact_type === "active_priority") {
      await onPriorityAnswer(
        {
          goal: String(data.get("goal")),
          target: String(data.get("target")),
          deadline: String(data.get("deadline")) || null,
        },
        remember,
      );
    } else if (isCommitmentFactType(output.fact_type)) {
      await onCommitmentAnswer(
        commitmentInputFromForm(output.fact_type, data),
        remember,
      );
    } else if (isIncomeFactType(output.fact_type)) {
      await onIncomeAnswer(
        incomeInputFromForm(output.fact_type, data),
        remember,
      );
    } else if (isConstraintFactType(output.fact_type)) {
      await onConstraintAnswer(
        constraintInputFromForm(output.fact_type, data),
        remember,
      );
    } else {
      await onEmergencyFundAnswer(
        {
          fact_type: output.fact_type,
          amount: Number(data.get("amount")),
        },
        remember,
      );
    }
  }

  const isObservationClarification =
    output.fact_type === "period_coverage" ||
    output.fact_type === "transaction_nature";

  return (
    <article className="space-y-4 rounded-xl border border-primary/30 bg-primary/5 p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>Clarification</Badge>
        <Badge variant="outline">{priorityLabels[output.priority]}</Badge>
        <Badge variant="outline">
          Question {output.question_number ?? 1} sur 3
        </Badge>
      </div>
      <div className="space-y-2">
        <h5 className="font-semibold">{output.question}</h5>
        <p className="text-sm">{output.observation}</p>
        <p className="text-sm text-muted-foreground">
          {output.possible_effect}
        </p>
      </div>
      {output.contradiction && (
        <dl className="grid gap-3 rounded-lg border bg-background/70 p-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="font-medium">Valeur déclarée</dt>
            <dd>{formatCurrency(output.contradiction.declared_value)}</dd>
          </div>
          <div>
            <dt className="font-medium">Dernière confirmation</dt>
            <dd>
              {formatAdviceTimestamp(output.contradiction.last_confirmed_at)}
            </dd>
          </div>
          <div>
            <dt className="font-medium">Signal</dt>
            <dd>{contradictionSignalLabels[output.contradiction.signal]}</dd>
          </div>
          <div>
            <dt className="font-medium">Période</dt>
            <dd>{output.contradiction.period.join(" → ")}</dd>
          </div>
          <div>
            <dt className="font-medium">Périmètre</dt>
            <dd>{output.contradiction.scope}</dd>
          </div>
          <div>
            <dt className="font-medium">Sujet affecté</dt>
            <dd>{output.contradiction.affected_subject}</dd>
          </div>
        </dl>
      )}
      {(output.transitions ?? []).map((transition) => (
        <Alert key={transition}>
          <AlertDescription>{transition}</AlertDescription>
        </Alert>
      ))}
      <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
        {output.material_effects.map((effect) => (
          <li key={effect}>{effect}</li>
        ))}
      </ul>
      {isObservationClarification ? (
        <Alert>
          <AlertDescription>
            Réponse durable, limitée à cette période ou aux transactions
            listées.
          </AlertDescription>
        </Alert>
      ) : (
        <Alert>
          <AlertDescription>
            Votre réponse sera réutilisée pour vos prochains conseils.
            Choisissez « Cette fois seulement » pour la limiter à cette session.
          </AlertDescription>
        </Alert>
      )}
      <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
        {output.contradiction ? (
          <div className="space-y-2">
            <Label htmlFor="contradiction-amount">Nouvelle valeur</Label>
            <Input
              id="contradiction-amount"
              name="amount"
              type="number"
              min="0.01"
              step="0.01"
              defaultValue={output.contradiction.observed_value}
              required
            />
          </div>
        ) : output.fact_type === "period_coverage" ? (
          <>
            <div className="space-y-2">
              <Label htmlFor="coverage-complete">Couverture</Label>
              <select
                id="coverage-complete"
                name="complete"
                value={coverageComplete ? "true" : "false"}
                onChange={(event) =>
                  setCoverageComplete(event.target.value === "true")
                }
                className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
              >
                <option value="true">Complète et sans trou</option>
                <option value="false">Incomplète</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="coverage-missing">
                Éléments manquants si incomplète
              </Label>
              <Input
                id="coverage-missing"
                name="missing_elements"
                required={!coverageComplete}
                placeholder="Compte joint, 12–18 octobre"
              />
            </div>
          </>
        ) : output.fact_type === "transaction_nature" ? (
          <>
            <div className="space-y-2">
              <Label htmlFor="transaction-nature">Nature</Label>
              <select
                id="transaction-nature"
                name="nature"
                defaultValue="expense"
                className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
              >
                <option value="income">Revenu</option>
                <option value="reimbursement">Remboursement</option>
                <option value="transfer">Transfert</option>
                <option value="expense">Dépense</option>
                <option value="debt_payment">Paiement de dette</option>
                <option value="saving">Épargne</option>
              </select>
            </div>
            {output.transaction_ids && output.transaction_ids.length > 1 ? (
              <div className="space-y-2">
                <Label htmlFor="transaction-scope">Portée</Label>
                <select
                  id="transaction-scope"
                  name="scope"
                  defaultValue="occurrence"
                  className="border-input bg-background h-9 w-full rounded-md border px-3 text-sm"
                >
                  <option value="occurrence">Cette occurrence</option>
                  <option value="series">
                    Uniquement les occurrences listées
                  </option>
                </select>
              </div>
            ) : (
              <input type="hidden" name="scope" value="occurrence" />
            )}
          </>
        ) : output.fact_type === "active_priority" ? (
          <>
            <div className="space-y-2">
              <Label htmlFor="priority-goal">Objectif courant</Label>
              <Input id="priority-goal" name="goal" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="priority-target">Cible</Label>
              <Input id="priority-target" name="target" required />
            </div>
            <div className="space-y-2">
              <Label htmlFor="priority-deadline">Échéance éventuelle</Label>
              <Input id="priority-deadline" name="deadline" type="date" />
            </div>
          </>
        ) : isCommitmentFactType(output.fact_type) ? (
          <CommitmentFields
            factType={output.fact_type}
            idPrefix={`clarification-${output.fact_type}`}
          />
        ) : isIncomeFactType(output.fact_type) ? (
          <IncomeFields
            factType={output.fact_type}
            idPrefix={`clarification-${output.fact_type}`}
          />
        ) : isConstraintFactType(output.fact_type) ? (
          <ConstraintFields
            factType={output.fact_type}
            idPrefix={`clarification-${output.fact_type}`}
          />
        ) : (
          <div className="space-y-2">
            <Label htmlFor={`clarification-${output.fact_type}-amount`}>
              {emergencyFundInputLabels[output.fact_type]}
            </Label>
            <Input
              id={`clarification-${output.fact_type}-amount`}
              name="amount"
              type="number"
              min="0"
              step="0.01"
              required
            />
          </div>
        )}
        <div className="flex flex-wrap items-end gap-2">
          {output.contradiction ? (
            <>
              <Button
                type="submit"
                name="resolution"
                value="confirm"
                disabled={isSubmitting}
              >
                Confirmer {formatCurrency(output.contradiction.declared_value)}
              </Button>
              <Button
                type="submit"
                name="resolution"
                value="correct"
                disabled={isSubmitting}
              >
                Corriger
              </Button>
              <Button
                type="submit"
                name="resolution"
                value="session"
                variant="outline"
                disabled={isSubmitting}
              >
                Cette fois seulement
              </Button>
            </>
          ) : (
            <>
              <Button
                type="submit"
                name="remember"
                value="true"
                disabled={isSubmitting}
              >
                {isObservationClarification
                  ? "Confirmer"
                  : "Répondre et réutiliser"}
              </Button>
              {!isObservationClarification && (
                <Button
                  type="submit"
                  name="remember"
                  value="false"
                  variant="outline"
                  disabled={isSubmitting}
                >
                  Cette fois seulement
                </Button>
              )}
            </>
          )}
        </div>
      </form>
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="ghost"
          onClick={() => onAbstain("unknown")}
          disabled={isSubmitting}
        >
          Je ne sais pas
        </Button>
        <Button
          type="button"
          variant="ghost"
          onClick={() => onAbstain("skip")}
          disabled={isSubmitting}
        >
          Passer
        </Button>
        {output.contradiction && (
          <Button
            type="button"
            variant="ghost"
            onClick={() => onAbstain("delete")}
            disabled={isSubmitting}
          >
            Supprimer
          </Button>
        )}
      </div>
    </article>
  );
}

function DecisionOutputCard({
  output,
  onCorrectSession,
}: {
  output: DecidedOutput;
  onCorrectSession: () => void;
}) {
  const title =
    output.type === "recommendation" ? output.action : output.conclusion;
  return (
    <article className="space-y-4 rounded-xl border bg-muted/20 p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="secondary">{outputLabels[output.type]}</Badge>
        <Badge variant="outline">{priorityLabels[output.priority]}</Badge>
        <Badge variant="outline">
          {uncertaintyLabels[output.trace.uncertainty.state]}
        </Badge>
      </div>
      <h5 className="font-semibold leading-relaxed">{title}</h5>
      {output.trace.summary !== output.trace.uncertainty.effect && (
        <p className="text-sm leading-relaxed text-muted-foreground">
          {output.trace.summary}
        </p>
      )}
      <p className="text-sm leading-relaxed text-muted-foreground">
        {output.trace.uncertainty.effect}
      </p>
      {output.type === "recommendation" && (
        <RecommendationMetadata output={output} />
      )}
      {output.type === "unresolved" &&
        output.conditional_branches.length > 0 && (
          <section className="space-y-2">
            <h6 className="text-sm font-medium">Branches explicatives</h6>
            <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
              {output.conditional_branches.map((branch) => (
                <li key={`${branch.condition}-${branch.effect}`}>
                  Si {branch.condition}, {branch.effect}.
                </li>
              ))}
            </ul>
          </section>
        )}
      <DecisionTraceDetails
        trace={output.trace}
        onCorrectSession={onCorrectSession}
      />
    </article>
  );
}

interface AdviceContentProps {
  advice: AdviceData;
  generatedAt: string | null;
  onRegenerate: () => void;
  isRegenerating: boolean;
  regenerateError: string | null;
  canRegenerate: boolean;
  onPriorityAnswer: (
    priority: ActivePriorityInput,
    rememberPriority: boolean,
  ) => Promise<void>;
  onEmergencyFundAnswer: (
    fact: EmergencyFundFactInput,
    rememberFact: boolean,
  ) => Promise<void>;
  onCommitmentAnswer: (
    fact: CommitmentFactInput,
    rememberFact: boolean,
  ) => Promise<void>;
  onIncomeAnswer: (
    fact: IncomeFactInput,
    rememberFact: boolean,
  ) => Promise<void>;
  onConstraintAnswer: (
    fact: ConstraintFactInput,
    rememberFact: boolean,
  ) => Promise<void>;
  onPeriodCoverageAnswer: (coverage: PeriodCoverageInput) => Promise<void>;
  onTransactionNatureAnswer: (fact: TransactionNatureInput) => Promise<void>;
  onClarificationAbstention: (
    action: "skip" | "unknown" | "delete",
  ) => Promise<void>;
  onCorrectSession: () => void;
}

function AdviceContent({
  advice,
  generatedAt,
  onRegenerate,
  isRegenerating,
  regenerateError,
  canRegenerate,
  onPriorityAnswer,
  onEmergencyFundAnswer,
  onCommitmentAnswer,
  onIncomeAnswer,
  onConstraintAnswer,
  onPeriodCoverageAnswer,
  onTransactionNatureAnswer,
  onClarificationAbstention,
  onCorrectSession,
}: AdviceContentProps) {
  const decidedOutputs = advice.outputs.filter(
    (output) => output.type !== "clarification",
  );
  const isTotalAbstention =
    !advice.outputs.some((output) => output.type === "clarification") &&
    decidedOutputs.length > 0 &&
    decidedOutputs.every((output) => output.type === "unresolved");

  return (
    <div className="space-y-6">
      {regenerateError && <ErrorAlert error={regenerateError} />}
      {isTotalAbstention && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <span className="block font-medium text-foreground">
              Abstention totale
            </span>
            Aucune recommandation ni conclusion sans action n’est suffisamment
            étayée.
          </AlertDescription>
        </Alert>
      )}
      <div className="space-y-4">
        {advice.outputs.map((output, index) =>
          output.type === "clarification" ? (
            <ClarificationCard
              key={`${index}-${output.fact_type}`}
              output={output}
              isSubmitting={isRegenerating}
              onPriorityAnswer={onPriorityAnswer}
              onEmergencyFundAnswer={onEmergencyFundAnswer}
              onCommitmentAnswer={onCommitmentAnswer}
              onIncomeAnswer={onIncomeAnswer}
              onConstraintAnswer={onConstraintAnswer}
              onPeriodCoverageAnswer={onPeriodCoverageAnswer}
              onTransactionNatureAnswer={onTransactionNatureAnswer}
              onAbstain={onClarificationAbstention}
            />
          ) : (
            <DecisionOutputCard
              key={index}
              output={output}
              onCorrectSession={onCorrectSession}
            />
          ),
        )}
      </div>
      {advice.clarification_trace.questions_consumed > 0 && (
        <aside
          aria-label="Trace des clarifications"
          className="space-y-2 rounded-lg border bg-muted/20 p-4 text-sm"
        >
          <p className="font-medium">
            {advice.clarification_trace.questions_consumed} question
            {advice.clarification_trace.questions_consumed > 1 ? "s" : ""} sur 3
            consommée
            {advice.clarification_trace.questions_consumed > 1 ? "s" : ""}
          </p>
          <ol className="list-decimal space-y-1 pl-5 text-muted-foreground">
            {advice.clarification_trace.questions.map((question) => (
              <li key={question.question_number}>
                {clarificationFactLabels[question.fact_type]} —{" "}
                {clarificationOutcomeLabels[question.outcome]}
              </li>
            ))}
          </ol>
          <p className="text-muted-foreground">
            {clarificationStopLabels[advice.clarification_trace.stop_reason]}
          </p>
        </aside>
      )}
      <Separator />
      <div className="flex items-center justify-between gap-4">
        {generatedAt && (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <CalendarDays className="h-4 w-4" />
            {t.advice.generated} {formatAdviceTimestamp(generatedAt)}
          </p>
        )}
        {canRegenerate && (
          <Button
            variant="outline"
            onClick={onRegenerate}
            disabled={isRegenerating}
            className="gap-2"
          >
            {isRegenerating ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                {t.advice.regenerating}
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4" />
                {t.advice.regenerate}
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
