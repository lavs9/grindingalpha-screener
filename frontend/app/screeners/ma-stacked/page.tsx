"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchMAStacked } from "@/lib/api/screeners";
import type { MAStackedStock, ScreenerResponse } from "@/lib/types/screener";
import { formatMarketCap } from "@/lib/utils";

// Column definitions for MA Stacked table
const columns: ColumnDef<MAStackedStock>[] = [
  {
    accessorKey: "symbol",
    header: ({ column }) => <SortableHeader column={column}>Symbol</SortableHeader>,
    cell: ({ row }) => (
      <div className="font-mono font-semibold">{row.getValue("symbol")}</div>
    ),
  },
  {
    accessorKey: "name",
    header: "Company Name",
    cell: ({ row }) => (
      <div className="max-w-[200px] truncate" title={row.getValue("name")}>
        {row.getValue("name")}
      </div>
    ),
  },
  {
    accessorKey: "rs_percentile",
    header: ({ column }) => <SortableHeader column={column}>RS %ile</SortableHeader>,
    cell: ({ row }) => {
      const rs = row.getValue("rs_percentile") as number;
      const isElite = rs >= 97;
      return (
        <Badge variant={isElite ? "default" : "secondary"} className="font-mono">
          {rs.toFixed(1)}
        </Badge>
      );
    },
  },
  {
    accessorKey: "vcp_score",
    header: ({ column }) => <SortableHeader column={column}>VCP Score</SortableHeader>,
    cell: ({ row }) => {
      const vcp = row.getValue("vcp_score") as number;
      let variant: "default" | "secondary" | "destructive" = "secondary";
      if (vcp >= 4) variant = "destructive"; // Strong VCP
      else if (vcp >= 3) variant = "default"; // Moderate VCP

      return (
        <Badge variant={variant} className="font-mono">
          {vcp}/5
        </Badge>
      );
    },
  },
  {
    accessorKey: "atr_extension",
    header: ({ column }) => <SortableHeader column={column}>ATR Ext %</SortableHeader>,
    cell: ({ row }) => {
      const atr = row.getValue("atr_extension") as number;
      const color = atr > 10 ? "text-orange-600" : atr > 5 ? "text-yellow-600" : "text-green-600";
      return (
        <div className={`font-mono ${color}`}>
          {atr.toFixed(2)}%
        </div>
      );
    },
  },
  {
    accessorKey: "darvas_position",
    header: ({ column }) => <SortableHeader column={column}>Darvas %</SortableHeader>,
    cell: ({ row }) => {
      const darvas = row.getValue("darvas_position") as number;
      const isNearHigh = darvas >= 90;
      return (
        <div className={`font-mono ${isNearHigh ? "text-green-600 font-semibold" : ""}`}>
          {darvas.toFixed(1)}%
        </div>
      );
    },
  },
  {
    accessorKey: "market_cap",
    header: ({ column }) => <SortableHeader column={column}>Market Cap</SortableHeader>,
    cell: ({ row }) => {
      const marketCap = row.getValue("market_cap") as number | null;
      return <div className="font-mono text-sm">{formatMarketCap(marketCap)}</div>;
    },
  },
  {
    accessorKey: "stage",
    header: "Stage",
    cell: ({ row }) => {
      const stage = row.getValue("stage") as number | null;
      if (stage == null) return <div className="text-muted-foreground">—</div>;

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
    header: "Stage Detail",
    cell: ({ row }) => {
      const detail = row.getValue("stage_detail") as string | null;
      return (
        <div className="text-sm text-muted-foreground max-w-[100px] truncate" title={detail || ""}>
          {detail || "—"}
        </div>
      );
    },
  },
];

export default function MAStackedPage() {
  const [data, setData] = React.useState<ScreenerResponse<MAStackedStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [minVcp, setMinVcp] = React.useState<string>("2");

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchMAStacked({
          minVcp: parseInt(minVcp) || 2,
        });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading MA Stacked data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [minVcp]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-96">
          <div className="text-muted-foreground">Loading MA Stacked data...</div>
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

  // Calculate statistics
  const avgRs = data.results.length > 0
    ? data.results.reduce((sum, stock) => sum + stock.rs_percentile, 0) / data.results.length
    : 0;
  const avgVcp = data.results.length > 0
    ? data.results.reduce((sum, stock) => sum + stock.vcp_score, 0) / data.results.length
    : 0;

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
        <h1 className="text-3xl font-bold mb-2">MA Stacked Breakouts</h1>
        <p className="text-muted-foreground">
          Stocks with perfect moving average alignment and tight consolidation patterns
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
            <CardTitle className="text-xl">{data.count}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Avg RS %ile</CardDescription>
            <CardTitle className="text-xl">{avgRs.toFixed(1)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Avg VCP Score</CardDescription>
            <CardTitle className="text-xl">{avgVcp.toFixed(1)}/5</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filter */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Filter</CardTitle>
          <CardDescription>
            Set minimum VCP score for consolidation quality
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            {/* Min VCP Filter */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Minimum VCP Score</label>
              <Input
                type="number"
                step="1"
                min="1"
                max="5"
                value={minVcp}
                onChange={(e) => setMinVcp(e.target.value)}
                className="w-[150px]"
                placeholder="2"
              />
            </div>

            {/* Info text */}
            <div className="text-sm text-muted-foreground">
              VCP Score 3-4 = Good setup, 5 = Ideal textbook VCP pattern
            </div>
          </div>
        </CardContent>
      </Card>

      {/* MA Stacked Table */}
      <Card>
        <CardHeader>
          <CardTitle>MA Stacked Stocks</CardTitle>
          <CardDescription>
            Stage 2 stocks with perfect MA alignment (8 &gt; 21 &gt; 50 &gt; 200 SMA) and VCP ≥{minVcp}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={data.results}
            searchKey="symbol"
            searchPlaceholder="Search symbol..."
          />
        </CardContent>
      </Card>

      {/* Legend */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Metrics Explained</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-3">
          <div>
            <strong>MA Stacked:</strong> Moving averages are in perfect bullish order
            (8 SMA &gt; 21 SMA &gt; 50 SMA &gt; 200 SMA). This indicates strong uptrend momentum
            and institutional support.
          </div>
          <div>
            <strong>VCP Score (Volatility Contraction Pattern):</strong> Measures quality of consolidation.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><Badge variant="secondary" className="text-xs">1-2</Badge> - Weak consolidation</li>
              <li><Badge variant="default" className="text-xs">3</Badge> - Moderate consolidation</li>
              <li><Badge variant="destructive" className="text-xs">4-5</Badge> - Strong VCP, ready for breakout</li>
            </ul>
          </div>
          <div>
            <strong>RS Percentile:</strong> Relative strength ranking vs all stocks. ≥97 = Elite performers
            (top 3% of market). These stocks are leading the market.
          </div>
          <div>
            <strong>ATR Extension %:</strong> How far price is from 50-day moving average in ATR units.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li className="text-green-600"><strong>&lt;5%:</strong> Near support, ideal entry zone</li>
              <li className="text-yellow-600"><strong>5-10%:</strong> Extended but acceptable</li>
              <li className="text-orange-600"><strong>&gt;10%:</strong> Overextended, wait for pullback</li>
            </ul>
          </div>
          <div>
            <strong>Darvas Position %:</strong> Where current price sits in Darvas box (52-week range).
            90-100% = Near all-time highs, breakout ready.
          </div>
          <div className="pt-2 border-t">
            <strong>Trading Strategy:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Best Setup:</strong> VCP ≥4, RS ≥97, Darvas ≥90%, ATR &lt;5% = High probability breakout</li>
              <li><strong>Entry:</strong> Buy on volume breakout above consolidation box</li>
              <li><strong>Stop Loss:</strong> Below recent swing low or 50 SMA</li>
              <li><strong>Risk:</strong> Avoid stocks with ATR &gt;10% (too extended from support)</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Pro Tip:</strong> Cross-reference with High Volume Movers to find MA Stacked stocks
            experiencing volume surge for highest conviction entries.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
