"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SCORE_COLORS, cn } from "@/lib/utils";
import type { ScoreLabel } from "@/types";

interface ScoreCardProps {
  score: number;
  scoreLabel: ScoreLabel | null;
  monthDisplay: string;
}

export function ScoreCard({ score, scoreLabel, monthDisplay }: ScoreCardProps) {
  const scoreColor = SCORE_COLORS[score];
  // [!]: Log unexpected score values for debugging.
  if (!scoreColor) {
    console.warn(`[ScoreCard] Unexpected score value: ${score}. Expected 0-3.`);
  }
  const finalColor = scoreColor || "bg-gray-500";

  return (
    <Card className="w-full">
      <CardContent className="flex items-center justify-between py-4">
        <span className="text-xl font-semibold capitalize">{monthDisplay}</span>
        <div className="flex items-center gap-3">
          <span className="text-lg font-medium">Score: {score}/3</span>
          {scoreLabel && (
            <Badge className={cn(finalColor, "text-white")}>{scoreLabel}</Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
