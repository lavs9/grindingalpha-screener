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
import { fetch4PercentBreakouts } from "@/lib/api/screeners";
import type { Breakout4PercentStock, ScreenerResponse } from "@/lib/types/screener";

// Column definitions for 4% Breakouts table
const columns: ColumnDef<Breakout4PercentStock>[] = [
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
    accessorKey: "change_1d_percent",
    header: ({ column }) => <SortableHeader column={column}>% Change</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1d_percent") as number;
      const isPositive = change >= 0;
      return (
        <div
          className={`font-mono font-semibold ${
            isPositive ? "text-green-600" : "text-red-600"
          }`}
        >
          {isPositive ? "+" : ""}
          {change.toFixed(2)}%
        </div>
      );
    },
  },
  {
    accessorKey: "rvol",
    header: ({ column }) => <SortableHeader column={column}>RVOL</SortableHeader>,
    cell: ({ row }) => {
      const rvol = row.getValue("rvol") as number | null;
      if (rvol == null) return <div className="text-muted-foreground">—</div>;
      const isHigh = rvol >= 2.0;
      return (
        <Badge variant={isHigh ? "default" : "secondary"} className="font-mono">
          {rvol.toFixed(2)}x
        </Badge>
      );
    },
  },
  {
    accessorKey: "volume",
    header: ({ column }) => <SortableHeader column={column}>Volume</SortableHeader>,
    cell: ({ row }) => {
      const vol = row.getValue("volume") as number;
      return (
        <div className="font-mono">
          {vol.toLocaleString('en-IN')}
        </div>
      );
    },
  },
  {
    accessorKey: "close",
    header: ({ column }) => <SortableHeader column={column}>Close</SortableHeader>,
    cell: ({ row }) => {
      const close = row.getValue("close") as number;
      return <div className="font-mono">₹{close.toFixed(2)}</div>;
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
        <div className="text-sm text-muted-foreground max-w-[150px] truncate" title={detail || ""}>
          {detail || "—"}
        </div>
      );
    },
  },
];

export default function Breakouts4PercentPage() {
  const [data, setData] = React.useState<ScreenerResponse<Breakout4PercentStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [minChange, setMinChange] = React.useState<string>("4.0");
  const [minRvol, setMinRvol] = React.useState<string>("1.5");

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch4PercentBreakouts({
          minChange: parseFloat(minChange) || 4.0,
          minRvol: parseFloat(minRvol) || 1.5,
        });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading 4% Breakouts:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [minChange, minRvol]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-96">
          <div className="text-muted-foreground">Loading breakout data...</div>
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
        <h1 className="text-3xl font-bold mb-2">4% Daily Breakouts</h1>
        <p className="text-muted-foreground">
          Momentum stocks with strong price moves and volume surge
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
            <CardDescription>Min % Change</CardDescription>
            <CardTitle className="text-xl">{minChange}%</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Min RVOL</CardDescription>
            <CardTitle className="text-xl">{minRvol}x</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
          <CardDescription>
            Customize the minimum thresholds for breakout detection
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            {/* Min Change Filter */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Minimum % Change</label>
              <Input
                type="number"
                step="0.5"
                min="1"
                max="20"
                value={minChange}
                onChange={(e) => setMinChange(e.target.value)}
                className="w-[150px]"
                placeholder="4.0"
              />
            </div>

            {/* Min RVOL Filter */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Minimum RVOL</label>
              <Input
                type="number"
                step="0.1"
                min="1"
                max="10"
                value={minRvol}
                onChange={(e) => setMinRvol(e.target.value)}
                className="w-[150px]"
                placeholder="1.5"
              />
            </div>

            {/* Info text */}
            <div className="text-sm text-muted-foreground">
              Higher values = stronger momentum and volume surge
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Breakouts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Breakout Stocks</CardTitle>
          <CardDescription>
            Stocks with ≥{minChange}% change and ≥{minRvol}x volume surge
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
            <strong>% Change:</strong> Daily percentage change in stock price. Positive (green) indicates gains.
          </div>
          <div>
            <strong>RVOL (Relative Volume):</strong> Today's volume relative to 50-day average.
            {" "}≥2.0x indicates strong institutional interest (highlighted in badge).
          </div>
          <div>
            <strong>Stage:</strong> Mark Minervini's stage analysis classification:
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><Badge className="bg-gray-500 text-xs">Stage 1</Badge> - Consolidation (below all MAs)</li>
              <li><Badge className="bg-green-500 text-xs">Stage 2</Badge> - Uptrend (above MAs, advancing)</li>
              <li><Badge className="bg-yellow-500 text-xs">Stage 3</Badge> - Distribution (topping, weakening)</li>
              <li><Badge className="bg-red-500 text-xs">Stage 4</Badge> - Decline (below MAs, falling)</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Trading Tip:</strong> Focus on Stage 2 stocks with RVOL ≥2.0x for highest probability setups.
            These combine strong price momentum with institutional buying pressure.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
