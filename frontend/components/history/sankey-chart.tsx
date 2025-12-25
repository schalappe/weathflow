"use client";

import React from "react";
import {
  Sankey,
  Tooltip,
  ResponsiveContainer,
  Layer,
  Rectangle,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { ErrorBoundary } from "@/components/ui/error-boundary";
import { CATEGORY_COLORS, formatCurrency, cn } from "@/lib/utils";
import { t } from "@/lib/translations";
import { GitBranch } from "lucide-react";
import type { CashFlowData, CategoryBreakdown } from "@/types";

interface SankeyChartProps {
  data: CashFlowData | null;
  className?: string;
}

interface SankeyNode {
  name: string;
  displayName: string;
  color: string;
  layer: number;
  value: number;
  // [>]: Store original values since Recharts modifies `value` during layout.
  originalAmount: number;
  percentage: number | null;
}

interface SankeyLink {
  source: number;
  target: number;
  value: number;
}

interface SankeyDataOutput {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

// [>]: Sort breakdown items by amount descending for consistent visual ordering.
function sortBreakdownByAmount(
  breakdown: CategoryBreakdown[],
): CategoryBreakdown[] {
  return [...breakdown].sort((a, b) => b.amount - a.amount);
}

// [>]: Transform API data to Recharts Sankey format.
// Flow: Income → Categories (Core/Choice/Compound) → Subcategories.
// Subcategories are sorted by amount (descending) within each category.
// When deficit > 0, show Deficit node instead of Compound.
// Pre-calculates percentages using total outflows so they sum to ~100%.
function transformToSankeyData(data: CashFlowData): SankeyDataOutput | null {
  if (data.income_total === 0) {
    return null;
  }

  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];
  const nodeMap = new Map<string, number>();

  // [>]: Calculate total outflows (what's actually displayed in the Sankey).
  // Using this instead of income_total ensures percentages sum to ~100%.
  const compoundOrDeficit =
    data.deficit > 0 ? data.deficit : data.compound_total;
  const totalOutflows = data.core_total + data.choice_total + compoundOrDeficit;

  // [>]: Helper to calculate percentage of total outflows.
  const calcPercentage = (amount: number): number =>
    totalOutflows > 0 ? Math.round((amount / totalOutflows) * 100) : 0;

  // [>]: Layer 0 - Income node (source).
  // Use totalOutflows for layout value so the Sankey is visually balanced.
  // Display the real income_total in originalAmount for the label.
  nodes.push({
    name: "income",
    displayName: t.categories.INCOME,
    color: CATEGORY_COLORS.INCOME,
    layer: 0,
    value: totalOutflows,
    originalAmount: data.income_total,
    percentage: null,
  });
  nodeMap.set("income", 0);

  // [>]: Layer 1 - Category nodes (Core, Choice, Compound/Deficit).
  if (data.core_total > 0) {
    const idx = nodes.length;
    nodes.push({
      name: "core",
      displayName: t.categories.CORE,
      color: CATEGORY_COLORS.CORE,
      layer: 1,
      value: data.core_total,
      originalAmount: data.core_total,
      percentage: calcPercentage(data.core_total),
    });
    nodeMap.set("core", idx);
    links.push({ source: 0, target: idx, value: data.core_total });
  }

  if (data.choice_total > 0) {
    const idx = nodes.length;
    nodes.push({
      name: "choice",
      displayName: t.categories.CHOICE,
      color: CATEGORY_COLORS.CHOICE,
      layer: 1,
      value: data.choice_total,
      originalAmount: data.choice_total,
      percentage: calcPercentage(data.choice_total),
    });
    nodeMap.set("choice", idx);
    links.push({ source: 0, target: idx, value: data.choice_total });
  }

  // [>]: Show Compound only when no deficit (user preference: replace Compound with Deficit).
  if (data.compound_total > 0 && data.deficit === 0) {
    const idx = nodes.length;
    nodes.push({
      name: "compound",
      displayName: t.categories.COMPOUND,
      color: CATEGORY_COLORS.COMPOUND,
      layer: 1,
      value: data.compound_total,
      originalAmount: data.compound_total,
      percentage: calcPercentage(data.compound_total),
    });
    nodeMap.set("compound", idx);
    links.push({ source: 0, target: idx, value: data.compound_total });
  }

  // [>]: Show Deficit node when overspending.
  if (data.deficit > 0) {
    const idx = nodes.length;
    nodes.push({
      name: "deficit",
      displayName: t.sankeyChart.deficit,
      color: "#c45a3b",
      layer: 1,
      value: data.deficit,
      originalAmount: data.deficit,
      percentage: calcPercentage(data.deficit),
    });
    nodeMap.set("deficit", idx);
    links.push({ source: 0, target: idx, value: data.deficit });
  }

  // [>]: Layer 2 - Subcategory nodes sorted by amount (descending).
  // Add Core subcategories first (sorted by amount).
  const sortedCoreBreakdown = sortBreakdownByAmount(data.core_breakdown);
  for (const breakdown of sortedCoreBreakdown) {
    const subcatName = `core_${breakdown.subcategory}`;
    const idx = nodes.length;
    const displayName =
      t.subcategories[breakdown.subcategory as keyof typeof t.subcategories] ||
      breakdown.subcategory;
    nodes.push({
      name: subcatName,
      displayName,
      color: CATEGORY_COLORS.CORE,
      layer: 2,
      value: breakdown.amount,
      originalAmount: breakdown.amount,
      percentage: null,
    });
    nodeMap.set(subcatName, idx);
    const coreIdx = nodeMap.get("core");
    if (coreIdx !== undefined) {
      links.push({ source: coreIdx, target: idx, value: breakdown.amount });
    }
  }

  // [>]: Add Choice subcategories (sorted by amount).
  const sortedChoiceBreakdown = sortBreakdownByAmount(data.choice_breakdown);
  for (const breakdown of sortedChoiceBreakdown) {
    const subcatName = `choice_${breakdown.subcategory}`;
    const idx = nodes.length;
    const displayName =
      t.subcategories[breakdown.subcategory as keyof typeof t.subcategories] ||
      breakdown.subcategory;
    nodes.push({
      name: subcatName,
      displayName,
      color: CATEGORY_COLORS.CHOICE,
      layer: 2,
      value: breakdown.amount,
      originalAmount: breakdown.amount,
      percentage: null,
    });
    nodeMap.set(subcatName, idx);
    const choiceIdx = nodeMap.get("choice");
    if (choiceIdx !== undefined) {
      links.push({ source: choiceIdx, target: idx, value: breakdown.amount });
    }
  }

  // [>]: Add Compound subcategories (only if no deficit, sorted by amount).
  if (data.deficit === 0) {
    const sortedCompoundBreakdown = sortBreakdownByAmount(
      data.compound_breakdown,
    );
    for (const breakdown of sortedCompoundBreakdown) {
      const subcatName = `compound_${breakdown.subcategory}`;
      const idx = nodes.length;
      const displayName =
        t.subcategories[
          breakdown.subcategory as keyof typeof t.subcategories
        ] || breakdown.subcategory;
      nodes.push({
        name: subcatName,
        displayName,
        color: CATEGORY_COLORS.COMPOUND,
        layer: 2,
        value: breakdown.amount,
        originalAmount: breakdown.amount,
        percentage: null,
      });
      nodeMap.set(subcatName, idx);
      const compoundIdx = nodeMap.get("compound");
      if (compoundIdx !== undefined) {
        links.push({
          source: compoundIdx,
          target: idx,
          value: breakdown.amount,
        });
      }
    }
  }

  // [>]: Return null if no flows to display.
  if (links.length === 0) {
    return null;
  }

  return { nodes, links };
}

// [>]: Calculate dynamic chart height based on number of subcategory nodes.
// Ensures enough vertical space for labels without overlap.
function calculateChartHeight(data: CashFlowData): number {
  const subcategoryCount =
    data.core_breakdown.length +
    data.choice_breakdown.length +
    (data.deficit === 0 ? data.compound_breakdown.length : 0);

  // [>]: Base height of 500px, add 40px per subcategory for two-line labels.
  const baseHeight = 500;
  const perSubcategoryHeight = 40;
  const calculatedHeight = baseHeight + subcategoryCount * perSubcategoryHeight;
  return Math.min(calculatedHeight, 900);
}

// [>]: Custom node renderer for Sankey diagram with category colors.
// Labels positioned based on layer: inside for categories, outside for subcategories.
// Category labels show name on first line, amount and percentage on second line.
function CustomNode(props: {
  x: number;
  y: number;
  width: number;
  height: number;
  index: number;
  payload: SankeyNode;
}): React.ReactElement<SVGElement> {
  const { x, y, width, height, payload } = props;

  // [!]: Return empty SVG group when payload undefined (satisfies Recharts type contract).
  if (!payload) {
    return <g />;
  }

  const isSubcategory = payload.layer === 2;
  const isIncome = payload.layer === 0;
  // [>]: Use originalAmount which is preserved from our data transformation.
  const formattedAmount = formatCurrency(payload.originalAmount);

  // [>]: Subcategory labels positioned outside on the right.
  // Two-line layout: name on top, amount below (same as categories).
  if (isSubcategory) {
    // [>]: Allow longer names since we have more right margin now.
    const maxNameLength = 28;
    const displayName =
      payload.displayName.length > maxNameLength
        ? payload.displayName.slice(0, maxNameLength) + "…"
        : payload.displayName;

    return (
      <Layer key={`CustomNode${props.index}`}>
        <Rectangle
          x={x}
          y={y}
          width={width}
          height={height}
          fill={payload.color}
          fillOpacity={0.85}
          radius={2}
        />
        <text
          textAnchor="start"
          x={x + width + 10}
          y={y + height / 2}
          fontSize={12}
          fill="currentColor"
          className="fill-foreground/90"
          fontWeight={500}
        >
          <tspan dy={-5}>{displayName}</tspan>
          <tspan
            x={x + width + 10}
            dy={16}
            fontSize={11}
            fontWeight={400}
            className="fill-foreground/60"
          >
            {formattedAmount}
          </tspan>
        </text>
      </Layer>
    );
  }

  // [>]: Income and Category labels with two-line layout.
  // Line 1: Category name (bold)
  // Line 2: Amount and percentage
  const hasPercentage = payload.percentage !== null;

  return (
    <Layer key={`CustomNode${props.index}`}>
      <Rectangle
        x={x}
        y={y}
        width={width}
        height={height}
        fill={payload.color}
        fillOpacity={0.9}
        radius={2}
      />
      {/* [>]: Two-line label: name on top, amount/percentage below */}
      <text
        textAnchor={isIncome ? "end" : "start"}
        x={isIncome ? x - 12 : x + width + 12}
        y={y + height / 2}
        fontSize={14}
        fill="currentColor"
        className="fill-foreground"
        fontWeight={600}
      >
        <tspan dy={-6}>{payload.displayName}</tspan>
        <tspan
          x={isIncome ? x - 12 : x + width + 12}
          dy={18}
          fontSize={12}
          fontWeight={500}
          className="fill-foreground/70"
        >
          {formattedAmount}
          {hasPercentage && ` (${payload.percentage}%)`}
        </tspan>
      </text>
    </Layer>
  );
}

// [>]: Custom link renderer with color based on source node.
function CustomLink(props: {
  sourceX: number;
  targetX: number;
  sourceY: number;
  targetY: number;
  sourceControlX: number;
  targetControlX: number;
  linkWidth: number;
  index: number;
  payload: { source: SankeyNode; target: SankeyNode };
}): React.ReactElement<SVGElement> {
  const {
    sourceX,
    targetX,
    sourceY,
    targetY,
    sourceControlX,
    targetControlX,
    linkWidth,
    payload,
  } = props;

  // [!]: Return empty SVG group when payload incomplete (satisfies Recharts type contract).
  if (!payload?.source?.color) {
    return <g />;
  }

  const halfWidth = linkWidth / 2;
  const path = `
    M${sourceX},${sourceY + halfWidth}
    C${sourceControlX},${sourceY + halfWidth} ${targetControlX},${targetY + halfWidth} ${targetX},${targetY + halfWidth}
    L${targetX},${targetY - halfWidth}
    C${targetControlX},${targetY - halfWidth} ${sourceControlX},${sourceY - halfWidth} ${sourceX},${sourceY - halfWidth}
    Z
  `;

  return (
    <Layer key={`CustomLink${props.index}`}>
      <path
        d={path}
        fill={payload.source.color}
        fillOpacity={0.4}
        stroke="none"
      />
    </Layer>
  );
}

// [>]: Custom tooltip content with formatted currency and percentage.
function CustomTooltipContent({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    payload: {
      source: SankeyNode;
      target: SankeyNode;
      value: number;
    };
  }>;
}) {
  if (!active || !payload?.length) return null;

  const linkData = payload[0]?.payload;
  // [!]: Verify all required properties exist before rendering.
  if (!linkData?.source?.displayName || !linkData?.target?.displayName) {
    return null;
  }

  // [>]: Use originalAmount from source node for accurate percentage calculation.
  const sourceOriginal = linkData.source.originalAmount;
  const targetOriginal = linkData.target.originalAmount;
  const percentage =
    sourceOriginal > 0
      ? Math.round((targetOriginal / sourceOriginal) * 100)
      : 0;

  return (
    <div className="rounded-lg border border-border/50 bg-background px-3 py-2.5 text-sm shadow-xl">
      <div className="flex items-center gap-2">
        <span
          style={{ color: linkData.source.color }}
          className="font-semibold"
        >
          {linkData.source.displayName}
        </span>
        <span className="text-muted-foreground">→</span>
        <span
          style={{ color: linkData.target.color }}
          className="font-semibold"
        >
          {linkData.target.displayName}
        </span>
      </div>
      <div className="mt-1.5 flex items-baseline gap-2">
        <span className="font-mono font-semibold tabular-nums text-foreground">
          {formatCurrency(targetOriginal)}
        </span>
        <span className="text-muted-foreground">
          ({percentage}% de {linkData.source.displayName})
        </span>
      </div>
    </div>
  );
}

const chartErrorFallback = (
  <div
    className="flex h-[300px] items-center justify-center text-muted-foreground"
    data-testid="chart-error"
  >
    {t.sankeyChart.error}
  </div>
);

export function SankeyChart({ data, className }: SankeyChartProps) {
  const sankeyData = data ? transformToSankeyData(data) : null;
  const isEmpty = !sankeyData;
  const chartHeight = data ? calculateChartHeight(data) : 450;

  return (
    <Card className={cn("border-0 shadow-lg", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#6a9bcc]/10 to-[#788c5d]/20">
            <GitBranch className="h-5 w-5 text-income-text" />
          </div>
          <div>
            <CardTitle className="text-base">{t.sankeyChart.title}</CardTitle>
            <CardDescription>{t.sankeyChart.subtitle}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ErrorBoundary fallback={chartErrorFallback}>
          {isEmpty ? (
            <div
              className="flex h-[500px] items-center justify-center text-muted-foreground"
              data-testid="empty-state"
            >
              {t.sankeyChart.empty}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={chartHeight}>
              <Sankey
                data={sankeyData}
                nodeWidth={20}
                nodePadding={36}
                linkCurvature={0.5}
                iterations={128}
                margin={{ left: 150, right: 250, top: 20, bottom: 20 }}
                node={CustomNode}
                link={CustomLink}
              >
                <Tooltip content={<CustomTooltipContent />} />
              </Sankey>
            </ResponsiveContainer>
          )}
        </ErrorBoundary>
      </CardContent>
    </Card>
  );
}
