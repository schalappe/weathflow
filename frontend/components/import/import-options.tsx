"use client";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
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
      <p className="text-sm font-medium text-foreground">Import mode</p>
      <RadioGroup
        value={mode}
        onValueChange={(value) => onModeChange(value as ImportMode)}
        disabled={isDisabled}
        className="flex flex-col gap-3"
      >
        <div className="flex items-start gap-3">
          <RadioGroupItem value="merge" id="merge" className="mt-0.5" />
          <Label htmlFor="merge" className="cursor-pointer">
            <span className="font-medium">Merge</span>
            <span className="block text-sm text-muted-foreground">
              Add new transactions, skip duplicates
            </span>
          </Label>
        </div>
        <div className="flex items-start gap-3">
          <RadioGroupItem value="replace" id="replace" className="mt-0.5" />
          <Label htmlFor="replace" className="cursor-pointer">
            <span className="font-medium">Replace</span>
            <span className="block text-sm text-muted-foreground">
              Delete existing data for selected months
            </span>
          </Label>
        </div>
      </RadioGroup>
    </div>
  );
}
