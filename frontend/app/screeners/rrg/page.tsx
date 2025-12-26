"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { RRGChart } from "@/components/charts/rrg-chart";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchRRGCharts } from "@/lib/api/screeners";
import type { RRGSector, RRGChartsResponse } from "@/lib/types/screener";

// Column definitions for sector details table
const columns: ColumnDef<RRGSector>[] = [
  {
    accessorKey: "index_symbol",
    header: ({ column }) => <SortableHeader column={column}>Index</SortableHeader>,
    cell: ({ row }) => (
      <div className="font-mono font-semibold">{row.getValue("index_symbol")}</div>
    ),
  },
  {
    accessorKey: "quadrant",
    header: "Quadrant",
    cell: ({ row }) => {
      const quadrant = row.getValue("quadrant") as string;
      const colors = {
        Leading: "bg-green-500",
        Weakening: "bg-yellow-500",
        Lagging: "bg-red-500",
        Improving: "bg-blue-500",
      };
      return (
        <Badge className={colors[quadrant as keyof typeof colors]}>
          {quadrant}
        </Badge>
      );
    },
  },
  {
    accessorKey: "rs_ratio",
    header: ({ column }) => <SortableHeader column={column}>RS-Ratio</SortableHeader>,
    cell: ({ row }) => {
      const ratio = row.getValue("rs_ratio") as number;
      return (
        <div className={`font-mono ${ratio > 100 ? "text-green-600" : "text-red-600"}`}>
          {ratio.toFixed(2)}
        </div>
      );
    },
  },
  {
    accessorKey: "rs_momentum",
    header: ({ column }) => <SortableHeader column={column}>RS-Momentum</SortableHeader>,
    cell: ({ row }) => {
      const momentum = row.getValue("rs_momentum") as number;
      return (
        <div className={`font-mono ${momentum > 0 ? "text-green-600" : "text-red-600"}`}>
          {momentum > 0 ? "+" : ""}
          {momentum.toFixed(2)}
        </div>
      );
    },
  },
  {
    accessorKey: "weekly_change_percent",
    header: ({ column }) => <SortableHeader column={column}>Weekly Change</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("weekly_change_percent") as number;
      return (
        <div className={`font-mono ${change >= 0 ? "text-green-600" : "text-red-600"}`}>
          {change >= 0 ? "+" : ""}
          {change.toFixed(2)}%
        </div>
      );
    },
  },
  {
    accessorKey: "current_close",
    header: ({ column }) => <SortableHeader column={column}>Close</SortableHeader>,
    cell: ({ row }) => {
      const close = row.getValue("current_close") as number;
      return <div className="font-mono">{close.toFixed(2)}</div>;
    },
  },
];

export default function RRGChartsPage() {
  const [data, setData] = React.useState<RRGChartsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchRRGCharts();
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading RRG Charts:", err);
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
          <div className="text-muted-foreground">Loading RRG data...</div>
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
        <h1 className="text-3xl font-bold mb-2">RRG Charts - Sector Rotation</h1>
        <p className="text-muted-foreground">
          Relative Rotation Graph showing sector strength vs {data.benchmark}
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
            <CardDescription>Total Indices</CardDescription>
            <CardTitle className="text-xl">{data.count}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Benchmark</CardDescription>
            <CardTitle className="text-xl">{data.benchmark}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Lookback</CardDescription>
            <CardTitle className="text-xl">{data.lookback_days} days</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Quadrant Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card className="border-green-500">
          <CardHeader className="pb-3">
            <CardDescription className="text-green-600">Leading</CardDescription>
            <CardTitle className="text-2xl">{data.quadrant_counts.Leading}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-yellow-500">
          <CardHeader className="pb-3">
            <CardDescription className="text-yellow-600">Weakening</CardDescription>
            <CardTitle className="text-2xl">{data.quadrant_counts.Weakening}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-red-500">
          <CardHeader className="pb-3">
            <CardDescription className="text-red-600">Lagging</CardDescription>
            <CardTitle className="text-2xl">{data.quadrant_counts.Lagging}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-blue-500">
          <CardHeader className="pb-3">
            <CardDescription className="text-blue-600">Improving</CardDescription>
            <CardTitle className="text-2xl">{data.quadrant_counts.Improving}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* RRG Scatter Plot */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>RRG Scatter Plot</CardTitle>
          <CardDescription>
            Sectors in the top-right (Leading) quadrant are outperforming with positive momentum
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RRGChart data={data.results} benchmark={data.benchmark} />
        </CardContent>
      </Card>

      {/* Sector Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>Sector Details</CardTitle>
          <CardDescription>
            Complete list of all sectoral indices with RRG metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={data.results}
            searchKey="index_symbol"
            searchPlaceholder="Search index..."
          />
        </CardContent>
      </Card>

      {/* Legend */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">RRG Quadrants Explained</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-3">
          <div className="flex items-start gap-3">
            <Badge className="bg-green-500 mt-0.5">Leading</Badge>
            <div>
              <strong>Top-Right:</strong> RS-Ratio &gt; 100, RS-Momentum &gt; 0. Sectors
              outperforming the benchmark with increasing strength. <strong>Buy/Hold</strong>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Badge className="bg-yellow-500 mt-0.5">Weakening</Badge>
            <div>
              <strong>Bottom-Right:</strong> RS-Ratio &gt; 100, RS-Momentum ≤ 0. Sectors still
              outperforming but losing momentum. <strong>Take profits</strong>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Badge className="bg-red-500 mt-0.5">Lagging</Badge>
            <div>
              <strong>Bottom-Left:</strong> RS-Ratio ≤ 100, RS-Momentum ≤ 0. Sectors
              underperforming with negative momentum. <strong>Avoid</strong>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Badge className="bg-blue-500 mt-0.5">Improving</Badge>
            <div>
              <strong>Top-Left:</strong> RS-Ratio ≤ 100, RS-Momentum &gt; 0. Sectors still
              underperforming but gaining momentum. <strong>Watch/Early entry</strong>
            </div>
          </div>
          <div className="pt-2 border-t">
            <strong>RS-Ratio:</strong> (Index/Benchmark) normalized to 100 baseline. Above 100 =
            outperforming.
            <br />
            <strong>RS-Momentum:</strong> Rate of change of RS-Ratio. Positive = gaining strength.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
