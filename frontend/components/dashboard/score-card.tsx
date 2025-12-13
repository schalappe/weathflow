"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ScoreLabel } from "@/types";
import { Sparkles, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface ScoreCardProps {
  score: number;
  scoreLabel: ScoreLabel | null;
  monthDisplay: string;
}

const SCORE_CONFIG: Record<
  number,
  { gradient: string; icon: React.ReactNode; description: string }
> = {
  3: {
    gradient: "score-gradient-great",
    icon: <Sparkles className="h-5 w-5" />,
    description: "Excellent budget control",
  },
  2: {
    gradient: "score-gradient-okay",
    icon: <TrendingUp className="h-5 w-5" />,
    description: "Good progress, room to improve",
  },
  1: {
    gradient: "score-gradient-need-improvement",
    icon: <TrendingDown className="h-5 w-5" />,
    description: "Some categories need attention",
  },
  0: {
    gradient: "score-gradient-poor",
    icon: <Minus className="h-5 w-5" />,
    description: "Budget targets not met",
  },
};

export function ScoreCard({ score, scoreLabel, monthDisplay }: ScoreCardProps) {
  const config = SCORE_CONFIG[score] || SCORE_CONFIG[0];

  return (
    <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-card via-card to-muted/30">
      {/* Background decoration */}
      <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-gradient-to-br from-violet-500/5 to-purple-500/10 blur-2xl" />
      <div className="absolute -bottom-4 -left-4 h-24 w-24 rounded-full bg-gradient-to-tr from-indigo-500/5 to-blue-500/10 blur-2xl" />

      <CardContent className="relative flex items-center justify-between p-6">
        {/* Month Display */}
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
            Current Period
          </span>
          <span className="text-2xl font-bold tracking-tight capitalize">
            {monthDisplay}
          </span>
        </div>

        {/* Score Badge */}
        <div className="flex items-center gap-4">
          {/* Score Indicator */}
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold tabular-nums tracking-tight">
                {score}
              </span>
              <span className="text-lg text-muted-foreground">/3</span>
            </div>
            <span className="text-xs text-muted-foreground">
              {config.description}
            </span>
          </div>

          {/* Score Label Badge */}
          {scoreLabel && (
            <div
              className={cn(
                "flex items-center gap-2 rounded-xl px-4 py-2.5 text-white shadow-lg",
                config.gradient,
              )}
            >
              {config.icon}
              <span className="text-sm font-semibold">{scoreLabel}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
