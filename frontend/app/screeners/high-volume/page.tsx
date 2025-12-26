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
import { fetchHighVolume } from "@/lib/api/screeners";
import type { HighVolumeStock, ScreenerResponse } from "@/lib/types/screener";

// Column definitions for High Volume table
const columns: ColumnDef<HighVolumeStock>[] = [
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
    accessorKey: "volume",
    header: ({ column }) => <SortableHeader column={column}>Volume</SortableHeader>,
    cell: ({ row }) => {
      const vol = row.getValue("volume") as number;
      return (
        <div className="font-mono font-semibold">
          {vol.toLocaleString('en-IN')}
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

      let variant: "default" | "secondary" | "destructive" = "secondary";
      if (rvol >= 3.0) variant = "destructive"; // Extremely high
      else if (rvol >= 2.0) variant = "default"; // High

      return (
        <Badge variant={variant} className="font-mono">
          {rvol.toFixed(2)}x
        </Badge>
      );
    },
  },
  {
    accessorKey: "change_1d_percent",
    header: ({ column }) => <SortableHeader column={column}>% Change</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1d_percent") as number | null;
      if (change == null) return <div className="text-muted-foreground">—</div>;
      const isPositive = change >= 0;
      return (
        <div
          className={`font-mono ${
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
    accessorKey: "close",
    header: ({ column }) => <SortableHeader column={column}>Close</SortableHeader>,
    cell: ({ row }) => {
      const close = row.getValue("close") as number;
      return <div className="font-mono">₹{close.toFixed(2)}</div>;
    },
  },
];

export default function HighVolumePage() {
  const [data, setData] = React.useState<ScreenerResponse<HighVolumeStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [minRvol, setMinRvol] = React.useState<string>("2.0");

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchHighVolume({
          minRvol: parseFloat(minRvol) || 2.0,
        });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading High Volume data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [minRvol]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-96">
          <div className="text-muted-foreground">Loading volume data...</div>
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
  const avgRvol = data.results.length > 0
    ? data.results.reduce((sum, stock) => sum + (stock.rvol || 0), 0) / data.results.length
    : 0;
  const maxRvol = data.results.length > 0
    ? Math.max(...data.results.map(s => s.rvol || 0))
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
        <h1 className="text-3xl font-bold mb-2">High Volume Movers</h1>
        <p className="text-muted-foreground">
          Stocks with unusual volume activity indicating institutional interest
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
            <CardDescription>Avg RVOL</CardDescription>
            <CardTitle className="text-xl">{avgRvol.toFixed(2)}x</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Max RVOL</CardDescription>
            <CardTitle className="text-xl">{maxRvol.toFixed(2)}x</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filter */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Filter</CardTitle>
          <CardDescription>
            Set minimum RVOL threshold for volume surge detection
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            {/* Min RVOL Filter */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Minimum RVOL</label>
              <Input
                type="number"
                step="0.5"
                min="1"
                max="10"
                value={minRvol}
                onChange={(e) => setMinRvol(e.target.value)}
                className="w-[150px]"
                placeholder="2.0"
              />
            </div>

            {/* Info text */}
            <div className="text-sm text-muted-foreground">
              RVOL ≥2.0x = High volume, ≥3.0x = Extremely high volume
            </div>
          </div>
        </CardContent>
      </Card>

      {/* High Volume Table */}
      <Card>
        <CardHeader>
          <CardTitle>Volume Surge Stocks</CardTitle>
          <CardDescription>
            Stocks with ≥{minRvol}x relative volume compared to 50-day average
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
            <strong>Volume:</strong> Total number of shares traded today. High absolute volume
            indicates strong participation and liquidity.
          </div>
          <div>
            <strong>RVOL (Relative Volume):</strong> Today's volume relative to 50-day average volume.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><Badge variant="secondary" className="text-xs">1.0-2.0x</Badge> - Above average volume</li>
              <li><Badge variant="default" className="text-xs">2.0-3.0x</Badge> - High volume (institutions likely active)</li>
              <li><Badge variant="destructive" className="text-xs">≥3.0x</Badge> - Extremely high volume (major event or news)</li>
            </ul>
          </div>
          <div>
            <strong>% Change:</strong> Daily price change. Volume surges often accompany significant price moves.
            Green = gains, Red = losses.
          </div>
          <div className="pt-2 border-t">
            <strong>Trading Interpretation:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>High volume + positive change:</strong> Strong buying pressure, bullish signal</li>
              <li><strong>High volume + negative change:</strong> Strong selling pressure, bearish signal</li>
              <li><strong>High volume + small change:</strong> Accumulation/distribution or indecision</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Pro Tip:</strong> Cross-reference with the 4% Breakouts screener to find stocks with
            both high volume AND strong price momentum for highest conviction setups.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
