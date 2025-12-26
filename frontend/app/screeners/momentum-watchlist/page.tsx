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
import { fetchMomentumWatchlist } from "@/lib/api/screeners";
import type { MomentumStock, ScreenerResponse } from "@/lib/types/screener";
import { formatMarketCap } from "@/lib/utils";

// Column definitions for Momentum Watchlist table
const columns: ColumnDef<MomentumStock>[] = [
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
      let variant: "default" | "secondary" | "destructive" = "secondary";
      if (rs >= 90) variant = "destructive"; // Elite
      else if (rs >= 80) variant = "default"; // Strong

      return (
        <Badge variant={variant} className="font-mono">
          {rs.toFixed(1)}
        </Badge>
      );
    },
  },
  {
    accessorKey: "atr_extension",
    header: ({ column }) => <SortableHeader column={column}>ATR Ext</SortableHeader>,
    cell: ({ row }) => {
      const atr = row.getValue("atr_extension") as number | null;
      if (atr == null) return <div className="text-muted-foreground">—</div>;

      // Color code: Green (near support), Yellow (moderate), Red (extended)
      const color = Math.abs(atr) <= 3 ? "text-green-600" : Math.abs(atr) <= 5 ? "text-yellow-600" : "text-orange-600";
      return (
        <div className={`font-mono ${color}`}>
          {atr.toFixed(2)}
        </div>
      );
    },
  },
  {
    accessorKey: "lod_atr_percent",
    header: ({ column }) => <SortableHeader column={column}>LoD ATR %</SortableHeader>,
    cell: ({ row }) => {
      const lod = row.getValue("lod_atr_percent") as number | null;
      const isTight = row.original.is_tight;

      if (lod == null) return <div className="text-muted-foreground">—</div>;

      return (
        <div className="flex items-center gap-2">
          <div className="font-mono">
            {lod.toFixed(1)}%
          </div>
          {isTight && (
            <Badge variant="default" className="text-xs">
              Tight
            </Badge>
          )}
        </div>
      );
    },
  },
  {
    accessorKey: "change_1d_percent",
    header: ({ column }) => <SortableHeader column={column}>% Change</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1d_percent") as number | null;
      const isGreen = row.original.is_green_candle;

      if (change == null) return <div className="text-muted-foreground">—</div>;

      return (
        <div className="flex items-center gap-2">
          <div
            className={`font-mono ${
              change >= 0 ? "text-green-600" : "text-red-600"
            }`}
          >
            {change >= 0 ? "+" : ""}
            {change.toFixed(2)}%
          </div>
          {isGreen && (
            <div className="w-2 h-2 rounded-full bg-green-500" title="Green candle (Close > Open)" />
          )}
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

export default function MomentumWatchlistPage() {
  const [data, setData] = React.useState<ScreenerResponse<MomentumStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [minRs, setMinRs] = React.useState<string>("70");
  const [maxLodAtr, setMaxLodAtr] = React.useState<string>("60");

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchMomentumWatchlist({
          minRs: parseFloat(minRs) || 70.0,
          maxLodAtr: parseFloat(maxLodAtr) || 60.0,
        });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading Momentum Watchlist data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [minRs, maxLodAtr]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-96">
          <div className="text-muted-foreground">Loading momentum watchlist...</div>
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
  const tightCount = data.results.filter(s => s.is_tight).length;

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
        <h1 className="text-3xl font-bold mb-2">Momentum Watchlist</h1>
        <p className="text-muted-foreground">
          High RS stocks near support with tight action, ready for swing entries
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
            <CardDescription>Tight Setups</CardDescription>
            <CardTitle className="text-xl">{tightCount}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
          <CardDescription>
            Customize minimum RS percentile and maximum LoD ATR threshold
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            {/* Min RS Filter */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Minimum RS Percentile</label>
              <Input
                type="number"
                step="5"
                min="50"
                max="95"
                value={minRs}
                onChange={(e) => setMinRs(e.target.value)}
                className="w-[180px]"
                placeholder="70"
              />
            </div>

            {/* Max LoD ATR Filter */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Max LoD ATR %</label>
              <Input
                type="number"
                step="10"
                min="20"
                max="100"
                value={maxLodAtr}
                onChange={(e) => setMaxLodAtr(e.target.value)}
                className="w-[180px]"
                placeholder="60"
              />
            </div>

            {/* Info text */}
            <div className="text-sm text-muted-foreground">
              RS ≥{minRs}, LoD ATR ≤{maxLodAtr}% = tight consolidation
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Momentum Watchlist Table */}
      <Card>
        <CardHeader>
          <CardTitle>Entry Candidates</CardTitle>
          <CardDescription>
            Stage 2+ stocks with RS ≥{minRs} near support (sorted by least extended)
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
            <strong>RS Percentile:</strong> Relative strength ranking vs all stocks.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><Badge variant="secondary" className="text-xs">70-80</Badge> - Strong performers</li>
              <li><Badge variant="default" className="text-xs">80-90</Badge> - Very strong</li>
              <li><Badge variant="destructive" className="text-xs">≥90</Badge> - Elite top 10%</li>
            </ul>
          </div>
          <div>
            <strong>ATR Extension:</strong> How far price is from 50 SMA in ATR units. Lower = closer to support.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li className="text-green-600"><strong>≤3 ATR:</strong> Near support, ideal entry zone</li>
              <li className="text-yellow-600"><strong>3-5 ATR:</strong> Moderate extension, acceptable</li>
              <li className="text-orange-600"><strong>&gt;5 ATR:</strong> Extended, wait for pullback</li>
            </ul>
          </div>
          <div>
            <strong>LoD ATR %:</strong> Low-of-Day to High-of-Day range as % of ATR. Lower = tighter action.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><Badge variant="default" className="text-xs">Tight</Badge> badge = LoD &lt;60% ATR (consolidating, low risk)</li>
              <li><strong>&lt;40%:</strong> Very tight, best setups</li>
              <li><strong>40-60%:</strong> Moderate range, acceptable</li>
              <li><strong>&gt;60%:</strong> Wide range, higher risk</li>
            </ul>
          </div>
          <div>
            <strong>% Change & Green Candle:</strong> Daily price change. Green dot = bullish candle (close &gt; open).
            Combination of positive change + green candle = buying pressure at support.
          </div>
          <div className="pt-2 border-t">
            <strong>Trading Strategy:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Best Setup:</strong> RS ≥85, ATR &lt;3, LoD Tight, Green Candle = High probability entry</li>
              <li><strong>Entry:</strong> Buy on breakout above recent consolidation high with volume</li>
              <li><strong>Stop Loss:</strong> Below low of consolidation or 50 SMA (whichever is higher)</li>
              <li><strong>Position Sizing:</strong> Tighter LoD ATR = smaller stop = larger position size</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Pro Tip:</strong> Monitor this watchlist daily. Stocks that appear repeatedly with tight LoD
            are building energy. Add volume surge (cross-reference with High Volume screener) for highest conviction entries.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
