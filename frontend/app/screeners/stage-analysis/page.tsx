"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchStageAnalysis } from "@/lib/api/screeners";
import type { StageBreakdown, StageAnalysisResponse } from "@/lib/types/screener";

// Column definitions for Stage Analysis table
const columns: ColumnDef<StageBreakdown>[] = [
  {
    accessorKey: "stage",
    header: "Stage",
    cell: ({ row }) => {
      const stage = row.getValue("stage") as number;
      const stageColors: Record<number, string> = {
        1: "bg-gray-500",
        2: "bg-green-500",
        3: "bg-yellow-500",
        4: "bg-red-500",
      };

      return (
        <Badge className={stageColors[stage] || "bg-gray-500"}>
          Stage {stage}
        </Badge>
      );
    },
  },
  {
    accessorKey: "stage_detail",
    header: "Detail",
    cell: ({ row }) => (
      <div className="font-medium">{row.getValue("stage_detail")}</div>
    ),
  },
  {
    accessorKey: "count",
    header: ({ column }) => <SortableHeader column={column}>Count</SortableHeader>,
    cell: ({ row }) => {
      const count = row.getValue("count") as number;
      return <div className="font-mono font-semibold">{count.toLocaleString()}</div>;
    },
  },
  {
    accessorKey: "percentage",
    header: ({ column }) => <SortableHeader column={column}>% of Total</SortableHeader>,
    cell: ({ row }) => {
      const pct = row.getValue("percentage") as number;
      const stage = row.original.stage;

      // Color code based on desirability (Stage 2 is best for longs)
      const color = stage === 2 ? "text-green-600" : stage === 3 ? "text-yellow-600" : "text-muted-foreground";

      return (
        <div className={`font-mono font-semibold ${color}`}>
          {pct.toFixed(2)}%
        </div>
      );
    },
  },
  {
    accessorKey: "tight_lod_count",
    header: ({ column }) => <SortableHeader column={column}>Tight Setups</SortableHeader>,
    cell: ({ row }) => {
      const tight = row.getValue("tight_lod_count") as number;
      const total = row.original.count;
      const pct = total > 0 ? (tight / total) * 100 : 0;

      return (
        <div className="flex flex-col gap-1">
          <div className="font-mono">{tight.toLocaleString()}</div>
          <div className="text-xs text-muted-foreground">
            ({pct.toFixed(0)}% of stage)
          </div>
        </div>
      );
    },
  },
  {
    accessorKey: "avg_lod_atr_percent",
    header: ({ column }) => <SortableHeader column={column}>Avg LoD ATR %</SortableHeader>,
    cell: ({ row }) => {
      const avg = row.getValue("avg_lod_atr_percent") as number;
      return (
        <div className="font-mono">
          {avg.toFixed(1)}%
        </div>
      );
    },
  },
];

export default function StageAnalysisPage() {
  const [data, setData] = React.useState<StageAnalysisResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchStageAnalysis();
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading Stage Analysis data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-96">
          <div className="text-muted-foreground">Loading stage analysis...</div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-96">
          <div className="text-destructive">Error: {error || "No data available"}</div>
        </div>
      </div>
    );
  }

  // Calculate totals by major stage
  const stageTotals = data.breakdown.reduce((acc, row) => {
    const existing = acc.find(s => s.stage === row.stage);
    if (existing) {
      existing.count += row.count;
      existing.percentage += row.percentage;
      existing.tight_lod_count += row.tight_lod_count;
    } else {
      acc.push({
        stage: row.stage,
        count: row.count,
        percentage: row.percentage,
        tight_lod_count: row.tight_lod_count,
      });
    }
    return acc;
  }, [] as Array<{ stage: number; count: number; percentage: number; tight_lod_count: number; }>);

  // Get Stage 2 stocks count
  const stage2Total = stageTotals.find(s => s.stage === 2);
  const stage2Count = stage2Total ? stage2Total.count : 0;
  const stage2Pct = stage2Total ? stage2Total.percentage : 0;

  return (
    <div className="container mx-auto py-8 px-4 max-w-[1400px]">
      {/* Header */}
      <div className="mb-6">
        <Link href="/">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">Stage Analysis Breakdown</h1>
        <p className="text-muted-foreground">
          Market-wide distribution of stocks across Mark Minervini's 4 stages
        </p>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Date</CardDescription>
            <CardTitle className="text-xl">{data.date}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Stocks</CardDescription>
            <CardTitle className="text-xl">{data.total_stocks.toLocaleString()}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Stage 2 (Uptrend)</CardDescription>
            <CardTitle className="text-xl text-green-600">{stage2Count} ({stage2Pct.toFixed(1)}%)</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Tight Setups</CardDescription>
            <CardTitle className="text-xl">{data.breakdown.reduce((sum, s) => sum + s.tight_lod_count, 0)}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Stage Distribution Visualization */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Stage Distribution</CardTitle>
          <CardDescription>Visual breakdown of market stages</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stageTotals.sort((a, b) => a.stage - b.stage).map((stageData) => {
              const stageColors: Record<number, { bg: string; text: string }> = {
                1: { bg: "bg-gray-500", text: "text-gray-700" },
                2: { bg: "bg-green-500", text: "text-green-700" },
                3: { bg: "bg-yellow-500", text: "text-yellow-700" },
                4: { bg: "bg-red-500", text: "text-red-700" },
              };
              const colors = stageColors[stageData.stage] || { bg: "bg-gray-500", text: "text-gray-700" };

              const stageNames: Record<number, string> = {
                1: "Consolidation",
                2: "Uptrend",
                3: "Distribution",
                4: "Decline",
              };

              return (
                <div key={stageData.stage} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge className={colors.bg}>
                        Stage {stageData.stage}
                      </Badge>
                      <span className="font-medium">{stageNames[stageData.stage]}</span>
                    </div>
                    <div className="text-sm font-mono">
                      {stageData.count.toLocaleString()} stocks ({stageData.percentage.toFixed(1)}%)
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                    <div
                      className={`h-full ${colors.bg} transition-all duration-500`}
                      style={{ width: `${stageData.percentage}%` }}
                    />
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {stageData.tight_lod_count} tight setups ({((stageData.tight_lod_count / stageData.count) * 100).toFixed(0)}% of stage)
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Stage Breakdown Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Stage Breakdown</CardTitle>
          <CardDescription>
            Stage-by-stage analysis with sub-stage details
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={data.breakdown}
            searchKey="stage_detail"
            searchPlaceholder="Search stage..."
          />
        </CardContent>
      </Card>

      {/* Legend */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Stage Analysis Guide</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-3">
          <div>
            <strong>Mark Minervini's 4 Stages:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><Badge className="bg-gray-500 text-xs">Stage 1</Badge> - <strong>Consolidation:</strong> Stock is basing,
              building energy. Price below all moving averages. Low volatility, tight range.</li>
              <li><Badge className="bg-green-500 text-xs">Stage 2</Badge> - <strong>Uptrend:</strong> Stock is advancing.
              Price above all MAs (8 &gt; 21 &gt; 50 &gt; 200 SMA). This is where money is made on the long side.</li>
              <li><Badge className="bg-yellow-500 text-xs">Stage 3</Badge> - <strong>Distribution:</strong> Stock is topping.
              Institutional selling into retail buying. Sideways action near highs, weakening momentum.</li>
              <li><Badge className="bg-red-500 text-xs">Stage 4</Badge> - <strong>Decline:</strong> Stock is falling.
              Price below moving averages. Avoid longs, consider shorts.</li>
            </ul>
          </div>
          <div>
            <strong>Stage 2 Sub-Stages:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>2A (Early):</strong> Just broke out of Stage 1. Best risk/reward for new entries.</li>
              <li><strong>2B (Middle):</strong> Strong uptrend momentum. Can still enter on pullbacks to support.</li>
              <li><strong>2C (Late):</strong> Extended move, approaching Stage 3. Tighten stops, prepare to exit.</li>
            </ul>
          </div>
          <div>
            <strong>Market Health Interpretation:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Bullish Market:</strong> &gt;30% of stocks in Stage 2. Strong foundation for longs.</li>
              <li><strong>Neutral Market:</strong> 20-30% in Stage 2. Selective opportunities.</li>
              <li><strong>Bearish Market:</strong> &lt;20% in Stage 2. Defensive positioning, favor cash/shorts.</li>
            </ul>
          </div>
          <div>
            <strong>Tight Setups:</strong> Stocks with LoD ATR &lt;60% (low intraday range). These are consolidating
            and offer better risk/reward due to tighter stops. Focus on Stage 2 tight setups for highest probability trades.
          </div>
          <div className="pt-2 border-t">
            <strong>Trading Strategy:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Stage 2A:</strong> Aggressive entries on breakouts or first pullback to 21 EMA.</li>
              <li><strong>Stage 2B:</strong> Enter on pullbacks to 50 SMA with volume confirmation.</li>
              <li><strong>Stage 3:</strong> Exit existing longs, take profits. Do not initiate new longs.</li>
              <li><strong>Stage 4:</strong> Avoid entirely for longs. May consider shorts if experienced.</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Pro Tip:</strong> Track this screener weekly to gauge overall market health. If Stage 2 percentage
            is declining week-over-week, reduce position sizes and tighten stops across your portfolio.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
