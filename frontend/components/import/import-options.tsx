"use client";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { t } from "@/lib/translations";
import type { ImportMode } from "@/types";

interface ImportOptionsProps {
  mode: ImportMode;
  onModeChange: (mode: ImportMode) => void;
  isDisabled: boolean;
}

export function ImportOptions({
  mode,
  onModeChange,
  isDisabled,
}: ImportOptionsProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-foreground">{t.importOptions.label}</p>
      <RadioGroup
        value={mode}
        onValueChange={(value) => onModeChange(value as ImportMode)}
        disabled={isDisabled}
        className="flex flex-col gap-3"
      >
        <div className="flex items-start gap-3">
          <RadioGroupItem value="merge" id="merge" className="mt-0.5" />
          <Label htmlFor="merge" className="cursor-pointer">
            <span className="font-medium">{t.importOptions.merge.title}</span>
            <span className="block text-sm text-muted-foreground">
              {t.importOptions.merge.description}
            </span>
          </Label>
        </div>
        <div className="flex items-start gap-3">
          <RadioGroupItem value="replace" id="replace" className="mt-0.5" />
          <Label htmlFor="replace" className="cursor-pointer">
            <span className="font-medium">{t.importOptions.replace.title}</span>
            <span className="block text-sm text-muted-foreground">
              {t.importOptions.replace.description}
            </span>
          </Label>
        </div>
      </RadioGroup>
    </div>
  );
}
