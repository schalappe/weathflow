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
function transformToSankeyData(data: CashFlowData): SankeyDataOutput | null {
  if (data.income_total === 0) {
    return null;
  }

  const nodes: SankeyNode[] = [];
  const links: SankeyLink[] = [];
  const nodeMap = new Map<string, number>();

  // [>]: Layer 0 - Income node (source).
  nodes.push({
    name: "income",
    displayName: t.categories.INCOME,
    color: CATEGORY_COLORS.INCOME,
    layer: 0,
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

  // [>]: Base height of 300px, add 28px per subcategory beyond 8.
  const baseHeight = 300;
  const extraHeight = Math.max(0, subcategoryCount - 8) * 28;
  return Math.min(baseHeight + extraHeight, 600);
}

// [>]: Custom node renderer for Sankey diagram with category colors.
// Labels positioned based on layer: inside for categories, outside for subcategories.
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

  // [>]: Subcategory labels positioned outside on the right.
  // Category labels centered inside the node.
  if (isSubcategory) {
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
          x={x + width + 8}
          y={y + height / 2}
          dy={4}
          fontSize={11}
          fill="currentColor"
          className="fill-foreground/80"
          fontWeight={400}
        >
          {payload.displayName}
        </text>
      </Layer>
    );
  }

  // [>]: Income label on the left side, category labels outside on right.
  // Category labels positioned outside to ensure visibility in both light/dark modes.
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
      <text
        textAnchor={isIncome ? "end" : "start"}
        x={isIncome ? x - 8 : x + width + 8}
        y={y + height / 2}
        dy={4}
        fontSize={12}
        fill="currentColor"
        className="fill-foreground/90"
        fontWeight={600}
      >
        {payload.displayName}
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

// [>]: Custom tooltip content with formatted currency.
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

  return (
    <div className="rounded-lg border border-border/50 bg-background px-3 py-2 text-xs shadow-xl">
      <div className="flex items-center gap-2">
        <span style={{ color: linkData.source.color }} className="font-medium">
          {linkData.source.displayName}
        </span>
        <span className="text-muted-foreground">→</span>
        <span style={{ color: linkData.target.color }} className="font-medium">
          {linkData.target.displayName}
        </span>
      </div>
      <div className="mt-1 font-mono font-medium tabular-nums">
        {formatCurrency(linkData.value)}
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
  const chartHeight = data ? calculateChartHeight(data) : 300;

  return (
    <Card className={cn("border-0 shadow-lg", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#6a9bcc]/10 to-[#788c5d]/20">
            <GitBranch className="h-5 w-5 text-[#6a9bcc] dark:text-[#7eacdb]" />
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
              className="flex h-[300px] items-center justify-center text-muted-foreground"
              data-testid="empty-state"
            >
              {t.sankeyChart.empty}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={chartHeight}>
              <Sankey
                data={sankeyData}
                nodeWidth={16}
                nodePadding={24}
                linkCurvature={0.5}
                iterations={128}
                margin={{ left: 70, right: 150, top: 10, bottom: 10 }}
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
