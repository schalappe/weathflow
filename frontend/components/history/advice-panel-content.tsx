"use client";

import { useReducer, useCallback, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  AlertCircle,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Sparkles,
  Upload,
  TrendingUp,
  TrendingDown,
  Repeat,
  Target,
  Trophy,
  Zap,
  Clock,
  Wallet,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { getAdvice, generateAdvice } from "@/lib/api-client";
import {
  cn,
  formatAdviceTimestamp,
  formatCurrency,
  getErrorMessage,
} from "@/lib/utils";
import { t } from "@/lib/translations";
import type {
  AdviceData,
  EligibilityInfo,
  ProblemArea,
  SpendingPattern,
  Recommendation,
  ProgressReview,
  MonthlyGoal,
} from "@/types";

type AdvicePanelState = "loading" | "loaded" | "empty" | "error";

interface AdviceState {
  panelState: AdvicePanelState;
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
      payload: {
        advice: AdviceData;
        generatedAt: string;
        eligibility: EligibilityInfo;
      };
    }
  | { type: "FETCH_EMPTY"; payload: { eligibility: EligibilityInfo } }
  | { type: "FETCH_ERROR"; payload: string }
  | { type: "REGENERATE_START" }
  | {
      type: "REGENERATE_SUCCESS";
      payload: { advice: AdviceData; generatedAt: string };
    }
  | { type: "REGENERATE_ERROR"; payload: string };

const initialState: AdviceState = {
  panelState: "loading",
  advice: null,
  generatedAt: null,
  isRegenerating: false,
  error: null,
  eligibility: null,
};

function adviceReducer(state: AdviceState, action: AdviceAction): AdviceState {
  switch (action.type) {
    case "FETCH_START":
      return { ...initialState, panelState: "loading" };

    case "FETCH_SUCCESS":
      return {
        ...state,
        panelState: "loaded",
        advice: action.payload.advice,
        generatedAt: action.payload.generatedAt,
        eligibility: action.payload.eligibility,
        error: null,
      };

    case "FETCH_EMPTY":
      return {
        ...state,
        panelState: "empty",
        eligibility: action.payload.eligibility,
        error: null,
      };

    case "FETCH_ERROR":
      return { ...state, panelState: "error", error: action.payload };

    case "REGENERATE_START":
      return { ...state, isRegenerating: true, error: null };

    case "REGENERATE_SUCCESS":
      return {
        ...state,
        panelState: "loaded",
        advice: action.payload.advice,
        generatedAt: action.payload.generatedAt,
        isRegenerating: false,
      };

    case "REGENERATE_ERROR":
      return { ...state, isRegenerating: false, error: action.payload };

    default:
      return state;
  }
}

function isTrendPositive(trend: string): boolean {
  return trend.startsWith("+");
}

function isTrendNegative(trend: string): boolean {
  return trend.startsWith("-");
}

interface AdvicePanelContentProps {
  year: number;
  month: number;
  className?: string;
}

export function AdvicePanelContent({
  year,
  month,
  className,
}: AdvicePanelContentProps) {
  const [state, dispatch] = useReducer(adviceReducer, initialState);
  // [>]: Eligibility now comes from backend response, not local calculation.
  const canGenerate = state.eligibility?.can_generate ?? false;

  useEffect(() => {
    dispatch({ type: "FETCH_START" });
  }, [year, month]);

  useEffect(() => {
    let isMounted = true;

    async function loadAdvice() {
      try {
        const response = await getAdvice(year, month);
        if (!isMounted) return;

        if (response.exists) {
          dispatch({
            type: "FETCH_SUCCESS",
            payload: {
              advice: response.advice,
              generatedAt: response.generated_at,
              eligibility: response.eligibility,
            },
          });
        } else {
          dispatch({
            type: "FETCH_EMPTY",
            payload: { eligibility: response.eligibility },
          });
        }
      } catch (error) {
        console.error("[AdvicePanelContent] Failed to load advice:", error);
        if (isMounted) {
          dispatch({
            type: "FETCH_ERROR",
            payload: getErrorMessage(error, t.advice.loadError),
          });
        }
      }
    }

    if (state.panelState === "loading") {
      loadAdvice();
    }

    return () => {
      isMounted = false;
    };
  }, [year, month, state.panelState]);

  const handleGenerate = useCallback(async () => {
    const isRegenerate = state.panelState === "loaded";
    dispatch({ type: "REGENERATE_START" });

    try {
      const response = await generateAdvice(year, month, isRegenerate);
      dispatch({
        type: "REGENERATE_SUCCESS",
        payload: {
          advice: response.advice,
          generatedAt: response.generated_at,
        },
      });
    } catch (error) {
      console.error("[AdvicePanelContent] Failed to generate advice:", error);
      dispatch({
        type: "REGENERATE_ERROR",
        payload: getErrorMessage(error, t.advice.generateError),
      });
    }
  }, [year, month, state.panelState]);

  const handleRetry = useCallback(() => {
    dispatch({ type: "FETCH_START" });
  }, []);

  return (
    <div className={cn("space-y-6", className)}>
      {/* Loading State */}
      {state.panelState === "loading" && <AdviceSkeletonLoader />}

      {/* Empty State */}
      {state.panelState === "empty" && (
        <EmptyState
          onGenerate={handleGenerate}
          isLoading={state.isRegenerating}
          canGenerate={canGenerate}
          error={state.error}
          eligibilityReason={state.eligibility?.reason ?? null}
        />
      )}

      {/* Error State */}
      {state.panelState === "error" && (
        <ErrorState error={state.error} onRetry={handleRetry} />
      )}

      {/* Loaded State */}
      {state.panelState === "loaded" && state.advice && (
        <AdviceContent
          advice={state.advice}
          generatedAt={state.generatedAt}
          onRegenerate={handleGenerate}
          isRegenerating={state.isRegenerating}
          regenerateError={state.error}
          canRegenerate={canGenerate}
        />
      )}
    </div>
  );
}

function AdviceSkeletonLoader() {
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
      <Separator />
      <div className="space-y-3">
        <Skeleton className="h-5 w-36" />
        <Skeleton className="h-12 w-full rounded-lg" />
        <Skeleton className="h-12 w-full rounded-lg" />
      </div>
      <Separator />
      <div className="space-y-3">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
      </div>
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
      {/* [>]: Show error banner when generation fails from empty state. */}
      {error && (
        <Alert
          variant="destructive"
          className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950 max-w-md"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500/10 to-purple-500/20">
        <Sparkles className="h-8 w-8 text-violet-600 dark:text-violet-400" />
      </div>
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">
          {canGenerate ? t.advice.empty.title : t.advice.notAvailable.title}
        </h3>
        <p className="text-muted-foreground max-w-sm mx-auto">
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
  const lowerError = error.toLowerCase();
  return (
    lowerError.includes("mois") ||
    lowerError.includes("month") ||
    lowerError.includes("donnees") ||
    lowerError.includes("data") ||
    lowerError.includes("not found") ||
    lowerError.includes("insufficient")
  );
}

interface ErrorStateProps {
  error: string | null;
  onRetry: () => void;
}

function ErrorState({ error, onRetry }: ErrorStateProps) {
  const needsImport = isDataRelatedError(error);

  return (
    <Alert
      variant="destructive"
      className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
    >
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <span>{error}</span>
        {needsImport ? (
          <Button variant="outline" size="sm" asChild className="gap-2">
            <Link href="/import">
              <Upload className="h-4 w-4" />
              {t.advice.importData}
            </Link>
          </Button>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="gap-2"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            {t.advice.retry}
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

interface ProblemAreaItemProps {
  area: ProblemArea;
  index: number;
}

function ProblemAreaItem({ area, index }: ProblemAreaItemProps) {
  const isUp = isTrendPositive(area.trend);
  const isDown = isTrendNegative(area.trend);

  return (
    <li className="rounded-xl bg-muted/50 px-5 py-4 transition-colors hover:bg-muted space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-medium">
          {index + 1}. {area.category}
        </span>
        <div className="flex items-center gap-3">
          <span className="font-semibold tabular-nums">
            {formatCurrency(area.amount)}
          </span>
          <span
            className={cn(
              "flex items-center gap-1 rounded-md px-2.5 py-1 text-sm font-medium",
              isUp && "bg-red-500/10 text-red-700 dark:text-red-400",
              isDown &&
                "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
              !isUp &&
                !isDown &&
                "bg-gray-500/10 text-gray-600 dark:text-gray-400",
            )}
          >
            {isUp && <TrendingUp className="h-3.5 w-3.5" />}
            {isDown && <TrendingDown className="h-3.5 w-3.5" />}
            {area.trend}
          </span>
        </div>
      </div>
      {(area.root_cause || area.impact) && (
        <div className="text-sm text-muted-foreground space-y-2 pl-4 border-l-2 border-muted-foreground/30">
          {area.root_cause && <p className="leading-relaxed">{area.root_cause}</p>}
          {area.impact && (
            <p className="text-amber-600 dark:text-amber-400 leading-relaxed">{area.impact}</p>
          )}
        </div>
      )}
    </li>
  );
}

// [>]: Spending pattern item for the new spending patterns section.
interface SpendingPatternItemProps {
  pattern: SpendingPattern;
}

function SpendingPatternItem({ pattern }: SpendingPatternItemProps) {
  return (
    <li className="rounded-xl bg-muted/50 px-5 py-4 transition-colors hover:bg-muted space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Repeat className="h-4.5 w-4.5 text-blue-500" />
          <span className="font-medium">{pattern.pattern_type}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            {pattern.occurrences}x/mois
          </span>
          <span className="font-semibold tabular-nums text-blue-600 dark:text-blue-400">
            {formatCurrency(pattern.monthly_cost)}
          </span>
        </div>
      </div>
      <p className="text-sm text-muted-foreground leading-relaxed">{pattern.description}</p>
      <p className="text-sm text-muted-foreground italic">
        {pattern.insight}
      </p>
    </li>
  );
}

// [>]: Recommendation item for the new structured recommendations.
interface RecommendationItemProps {
  recommendation: Recommendation;
}

function RecommendationItem({ recommendation }: RecommendationItemProps) {
  return (
    <li className="rounded-xl bg-muted/30 p-5 space-y-3">
      <div className="flex items-start gap-3">
        <span className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
          {recommendation.priority}
        </span>
        <div className="flex-1 space-y-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium">{recommendation.action}</span>
            {recommendation.quick_win && (
              <Badge
                variant="secondary"
                className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 gap-1"
              >
                <Zap className="h-3.5 w-3.5" />
                {t.advice.quickWin}
              </Badge>
            )}
            <Badge
              variant="outline"
              className={cn(
                recommendation.difficulty === "Facile" &&
                  "border-green-500/50 text-green-600 dark:text-green-400",
                recommendation.difficulty === "Modéré" &&
                  "border-amber-500/50 text-amber-600 dark:text-amber-400",
                recommendation.difficulty === "Exigeant" &&
                  "border-red-500/50 text-red-600 dark:text-red-400",
              )}
            >
              {recommendation.difficulty}
            </Badge>
          </div>
          <p className="text-[15px] text-muted-foreground leading-relaxed">
            {recommendation.details}
          </p>
          <div className="flex items-center gap-1.5 text-sm text-emerald-600 dark:text-emerald-400">
            <Wallet className="h-4 w-4" />
            <span>
              {t.advice.expectedSavings}: {recommendation.expected_savings}
            </span>
          </div>
        </div>
      </div>
    </li>
  );
}

// [>]: Progress review section component.
interface ProgressReviewSectionProps {
  progressReview: ProgressReview;
}

function ProgressReviewSection({ progressReview }: ProgressReviewSectionProps) {
  return (
    <div className="space-y-4">
      <p className="text-[15px] text-muted-foreground leading-relaxed">
        {progressReview.previous_advice_followed}
      </p>

      {progressReview.wins.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 text-sm font-medium text-emerald-600 dark:text-emerald-400">
            <Trophy className="h-4 w-4" />
            {t.advice.wins}
          </div>
          <ul className="space-y-2">
            {progressReview.wins.map((win, index) => (
              <li
                key={index}
                className="text-[15px] text-muted-foreground flex items-start gap-2.5"
              >
                <CheckCircle2 className="h-4.5 w-4.5 text-emerald-500 flex-shrink-0 mt-0.5" />
                {win}
              </li>
            ))}
          </ul>
        </div>
      )}

      {progressReview.areas_for_growth.length > 0 && (
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 text-sm font-medium text-amber-600 dark:text-amber-400">
            <Target className="h-4 w-4" />
            {t.advice.areasForGrowth}
          </div>
          <ul className="space-y-2">
            {progressReview.areas_for_growth.map((area, index) => (
              <li
                key={index}
                className="text-[15px] text-muted-foreground flex items-start gap-2.5"
              >
                <Clock className="h-4.5 w-4.5 text-amber-500 flex-shrink-0 mt-0.5" />
                {area}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// [>]: Monthly goal section component.
interface MonthlyGoalSectionProps {
  monthlyGoal: MonthlyGoal;
}

function MonthlyGoalSection({ monthlyGoal }: MonthlyGoalSectionProps) {
  return (
    <div className="rounded-xl bg-gradient-to-r from-violet-500/10 to-purple-500/10 p-5 space-y-3">
      <div className="flex items-center justify-between gap-4">
        <span className="font-medium leading-snug">{monthlyGoal.objective}</span>
        <Badge
          variant="secondary"
          className="bg-violet-500/20 text-violet-700 dark:text-violet-300 flex-shrink-0"
        >
          {t.advice.targetAmount}: {formatCurrency(monthlyGoal.target_amount)}
        </Badge>
      </div>
      <p className="text-[15px] text-muted-foreground leading-relaxed">{monthlyGoal.strategy}</p>
    </div>
  );
}

interface AdviceContentProps {
  advice: AdviceData;
  generatedAt: string | null;
  onRegenerate: () => void;
  isRegenerating: boolean;
  regenerateError: string | null;
  canRegenerate: boolean;
}

function AdviceContent({
  advice,
  generatedAt,
  onRegenerate,
  isRegenerating,
  regenerateError,
  canRegenerate,
}: AdviceContentProps) {
  return (
    <div className="space-y-6">
      {/* Regenerate error banner */}
      {regenerateError && (
        <Alert
          variant="destructive"
          className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950"
        >
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{regenerateError}</AlertDescription>
        </Alert>
      )}

      {/* Analysis Section */}
      <section className="space-y-4">
        <div className="flex items-center gap-2.5">
          <BarChart3 className="h-5 w-5 text-violet-600 dark:text-violet-400" />
          <h4 className="text-lg font-semibold">{t.advice.sections.analysis}</h4>
        </div>
        <p className="text-[15px] text-muted-foreground leading-relaxed">
          {advice.analysis}
        </p>
      </section>

      {/* Spending Patterns Section */}
      {advice.spending_patterns && advice.spending_patterns.length > 0 && (
        <>
          <Separator />
          <section className="space-y-4">
            <div className="flex items-center gap-2.5">
              <Repeat className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              <h4 className="text-lg font-semibold">
                {t.advice.sections.spendingPatterns}
              </h4>
            </div>
            <ul className="space-y-3">
              {advice.spending_patterns.map((pattern, index) => (
                <SpendingPatternItem key={index} pattern={pattern} />
              ))}
            </ul>
          </section>
        </>
      )}

      {/* Problem Areas Section */}
      {advice.problem_areas.length > 0 && (
        <>
          <Separator />
          <section className="space-y-4">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              <h4 className="text-lg font-semibold">{t.advice.sections.problems}</h4>
            </div>
            <ul className="space-y-3">
              {advice.problem_areas.map((area, index) => (
                <ProblemAreaItem key={index} area={area} index={index} />
              ))}
            </ul>
          </section>
        </>
      )}

      {/* Recommendations Section */}
      {advice.recommendations.length > 0 && (
        <>
          <Separator />
          <section className="space-y-4">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
              <h4 className="text-lg font-semibold">
                {t.advice.sections.recommendations}
              </h4>
            </div>
            <ol className="space-y-4">
              {advice.recommendations.map((rec, index) => (
                <RecommendationItem key={index} recommendation={rec} />
              ))}
            </ol>
          </section>
        </>
      )}

      {/* Progress Review Section */}
      {advice.progress_review && (
        <>
          <Separator />
          <section className="space-y-4">
            <div className="flex items-center gap-2.5">
              <Trophy className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              <h4 className="text-lg font-semibold">
                {t.advice.sections.progressReview}
              </h4>
            </div>
            <ProgressReviewSection progressReview={advice.progress_review} />
          </section>
        </>
      )}

      {/* Monthly Goal Section */}
      {advice.monthly_goal && (
        <>
          <Separator />
          <section className="space-y-4">
            <div className="flex items-center gap-2.5">
              <Target className="h-5 w-5 text-violet-600 dark:text-violet-400" />
              <h4 className="text-lg font-semibold">{t.advice.sections.monthlyGoal}</h4>
            </div>
            <MonthlyGoalSection monthlyGoal={advice.monthly_goal} />
          </section>
        </>
      )}

      {/* Encouragement Section */}
      <Separator />
      <section className="space-y-4">
        <div className="flex items-center gap-2.5">
          <Sparkles className="h-5 w-5 text-violet-600 dark:text-violet-400" />
          <h4 className="text-lg font-semibold">{t.advice.sections.encouragement}</h4>
        </div>
        <p className="text-[15px] text-muted-foreground leading-relaxed">
          {advice.encouragement}
        </p>
      </section>

      {/* Footer with timestamp and regenerate button */}
      <div className="flex items-center justify-between border-t pt-5 mt-2">
        {generatedAt && (
          <p className="text-sm text-muted-foreground">
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
