"use client";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Lightbulb } from "lucide-react";
import { cn } from "@/lib/utils";
import { t } from "@/lib/translations";
import { AdvicePanelContent } from "./advice-panel-content";

interface AdvicePanelProps {
  year: number;
  month: number;
  className?: string;
}

export function AdvicePanel({ year, month, className }: AdvicePanelProps) {
  return (
    <Card className={cn("border-0 shadow-lg", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500/10 to-orange-500/20">
            <Lightbulb className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <CardTitle className="text-lg">{t.advice.title}</CardTitle>
            <CardDescription>{t.advice.subtitle}</CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <AdvicePanelContent year={year} month={month} />
      </CardContent>
    </Card>
  );
}
