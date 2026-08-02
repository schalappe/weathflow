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
  deleteEmergencyFundFact,
  generateAdvice,
  getEmergencyFundContext,
  getActivePriority,
  getAdvice,
  putActivePriority,
  putEmergencyFundFact,
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
  EmergencyFundFact,
  EmergencyFundFactInput,
  EmergencyFundFactType,
  ClarificationOutput,
  DecisionOutput,
  DecisionPriority,
  DecisionTrace,
  EligibilityInfo,
  RecommendationOutput,
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
  const [contextError, setContextError] = useState<string | null>(null);
  const canGenerate = state.eligibility?.can_generate ?? false;

  useEffect(() => {
    let active = true;
    dispatch({ type: "FETCH_START" });
    Promise.all([getActivePriority(), getEmergencyFundContext()])
      .then(([{ priority }, { facts }]) => {
        if (active) {
          setActivePriority(priority);
          setEmergencyFundFacts(facts);
          setContextError(null);
        }
      })
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

  const handlePriorityAnswer = useCallback(
    async (priority: ActivePriorityInput, rememberPriority: boolean) => {
      dispatch({ type: "REGENERATE_START" });
      try {
        const response = await generateAdvice(year, month, {
          regenerate: true,
          activePriority: priority,
          rememberPriority,
        });
        dispatch({
          type: "REGENERATE_SUCCESS",
          advice: response.advice,
          generatedAt: response.generated_at,
        });
        const context = await getActivePriority();
        setActivePriority(context.priority);
      } catch (error) {
        dispatch({
          type: "REGENERATE_ERROR",
          error: getErrorMessage(error, t.advice.generateError),
        });
      }
    },
    [year, month],
  );

  const handleEmergencyFundAnswer = useCallback(
    async (fact: EmergencyFundFactInput, rememberFact: boolean) => {
      dispatch({ type: "REGENERATE_START" });
      try {
        const response = await generateAdvice(year, month, {
          regenerate: true,
          emergencyFundFact: fact,
          rememberFact,
        });
        dispatch({
          type: "REGENERATE_SUCCESS",
          advice: response.advice,
          generatedAt: response.generated_at,
        });
        const context = await getEmergencyFundContext();
        setEmergencyFundFacts(context.facts);
      } catch (error) {
        dispatch({
          type: "REGENERATE_ERROR",
          error: getErrorMessage(error, t.advice.generateError),
        });
      }
    },
    [year, month],
  );

  const handleClarificationAbstention = useCallback(
    async (clarificationAction: "skip" | "unknown") => {
      dispatch({ type: "REGENERATE_START" });
      try {
        const response = await generateAdvice(year, month, {
          regenerate: true,
          clarificationAction,
        });
        dispatch({
          type: "REGENERATE_SUCCESS",
          advice: response.advice,
          generatedAt: response.generated_at,
        });
      } catch (error) {
        dispatch({
          type: "REGENERATE_ERROR",
          error: getErrorMessage(error, t.advice.generateError),
        });
      }
    },
    [year, month],
  );

  const handlePriorityCorrection = useCallback(
    async (priority: ActivePriorityInput) => {
      try {
        const response = await putActivePriority(priority);
        setActivePriority(response.priority);
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

  return (
    <div className={cn("space-y-6", className)}>
      <ActivePriorityPanel
        priority={activePriority}
        error={contextError}
        onCorrect={handlePriorityCorrection}
        onDelete={handlePriorityDeletion}
      />
      <EmergencyFundFactsPanel
        facts={emergencyFundFacts}
        onCorrect={handleEmergencyFundCorrection}
        onDelete={handleEmergencyFundDeletion}
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
                    {fact.valid_until
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
                        fact.fact_type === "active_priority"
                          ? "#active-priority-context"
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
          title={t.advice.conventions}
          items={trace.details.conventions}
          icon={<Scale className="h-4 w-4" />}
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
  onAbstain: (action: "skip" | "unknown") => Promise<void>;
}

function ClarificationCard({
  output,
  isSubmitting,
  onPriorityAnswer,
  onEmergencyFundAnswer,
  onAbstain,
}: ClarificationCardProps) {
  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const submitter = (event.nativeEvent as SubmitEvent)
      .submitter as HTMLButtonElement | null;
    const remember = submitter?.value === "true";
    if (output.fact_type === "active_priority") {
      await onPriorityAnswer(
        {
          goal: String(data.get("goal")),
          target: String(data.get("target")),
          deadline: String(data.get("deadline")) || null,
        },
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

  return (
    <article className="space-y-4 rounded-xl border border-primary/30 bg-primary/5 p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>Clarification</Badge>
        <Badge variant="outline">{priorityLabels[output.priority]}</Badge>
      </div>
      <div className="space-y-2">
        <h5 className="font-semibold">{output.question}</h5>
        <p className="text-sm">{output.observation}</p>
        <p className="text-sm text-muted-foreground">
          {output.possible_effect}
        </p>
      </div>
      <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
        {output.material_effects.map((effect) => (
          <li key={effect}>{effect}</li>
        ))}
      </ul>
      <Alert>
        <AlertDescription>
          Votre réponse sera réutilisée pour vos prochains conseils. Choisissez
          « Cette fois seulement » pour la limiter à cette session.
        </AlertDescription>
      </Alert>
      <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
        {output.fact_type === "active_priority" ? (
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
          <Button
            type="submit"
            name="remember"
            value="true"
            disabled={isSubmitting}
          >
            Répondre et réutiliser
          </Button>
          <Button
            type="submit"
            name="remember"
            value="false"
            variant="outline"
            disabled={isSubmitting}
          >
            Cette fois seulement
          </Button>
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
      </div>
      <h5 className="font-semibold leading-relaxed">{title}</h5>
      <p className="text-sm leading-relaxed text-muted-foreground">
        {output.trace.summary}
      </p>
      {output.type === "recommendation" && (
        <RecommendationMetadata output={output} />
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
  onClarificationAbstention: (action: "skip" | "unknown") => Promise<void>;
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
  onClarificationAbstention,
  onCorrectSession,
}: AdviceContentProps) {
  return (
    <div className="space-y-6">
      {regenerateError && <ErrorAlert error={regenerateError} />}
      <div className="space-y-4">
        {advice.outputs.map((output, index) =>
          output.type === "clarification" ? (
            <ClarificationCard
              key={index}
              output={output}
              isSubmitting={isRegenerating}
              onPriorityAnswer={onPriorityAnswer}
              onEmergencyFundAnswer={onEmergencyFundAnswer}
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
