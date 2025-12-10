"use client";

import {
  PieChart,
  Pie,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CATEGORY_COLORS, formatCurrency } from "@/lib/utils";

interface SpendingPieChartProps {
  core: number;
  choice: number;
  compound: number;
}

export function SpendingPieChart({
  core,
  choice,
  compound,
}: SpendingPieChartProps) {
  const data = [
    { name: "Core", value: Math.abs(core), color: CATEGORY_COLORS.CORE },
    { name: "Choice", value: Math.abs(choice), color: CATEGORY_COLORS.CHOICE },
    {
      name: "Compound",
      value: Math.abs(compound),
      color: CATEGORY_COLORS.COMPOUND,
    },
  ];

  const isEmpty = data.every((d) => d.value === 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Spending Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        {isEmpty ? (
          <div
            className="flex h-[200px] items-center justify-center text-muted-foreground"
            data-testid="empty-state"
          >
            No spending data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
