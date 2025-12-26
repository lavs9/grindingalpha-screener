"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchRSLeaders } from "@/lib/api/screeners";
import type { RSLeaderStock } from "@/lib/types/screener";
import { formatMarketCap } from "@/lib/utils";

// Column definitions for RS Leaders table
const columns: ColumnDef<RSLeaderStock>[] = [
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
      return (
        <Badge variant={rs >= 97 ? "default" : "secondary"} className="font-mono">
          {rs.toFixed(2)}%
        </Badge>
      );
    },
  },
  {
    accessorKey: "vars_score",
    header: ({ column }) => <SortableHeader column={column}>VARS</SortableHeader>,
    cell: ({ row }) => {
      const vars = row.getValue("vars_score") as number;
      return <div className="font-mono">{vars != null ? vars.toFixed(2) : "—"}</div>;
    },
  },
  {
    accessorKey: "change_1m_percent",
    header: ({ column }) => <SortableHeader column={column}>1M Change</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1m_percent") as number | null;
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
    accessorKey: "change_1w_percent",
    header: ({ column }) => <SortableHeader column={column}>1W Change</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1w_percent") as number | null;
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
    accessorKey: "market_cap",
    header: ({ column }) => <SortableHeader column={column}>Market Cap</SortableHeader>,
    cell: ({ row }) => {
      const marketCap = row.getValue("market_cap") as number | null;
      return <div className="font-mono text-sm">{formatMarketCap(marketCap)}</div>;
    },
    filterFn: (row, columnId, filterValue) => {
      const marketCap = row.getValue(columnId) as number | null;
      if (marketCap === null) return false;

      const [min, max] = filterValue as [number | undefined, number | undefined];
      if (min !== undefined && marketCap < min) return false;
      if (max !== undefined && marketCap > max) return false;
      return true;
    },
  },
  {
    accessorKey: "stage_detail",
    header: "Stage",
    cell: ({ row }) => {
      const stage = row.getValue("stage_detail") as string;
      return <Badge variant="outline">{stage}</Badge>;
    },
  },
];

export default function RSLeadersPage() {
  const [data, setData] = React.useState<RSLeaderStock[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [screenerInfo, setScreenerInfo] = React.useState<{
    date: string;
    count: number;
  } | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchRSLeaders();
        setData(response.results);
        setScreenerInfo({
          date: response.date,
          count: response.count,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading RS Leaders:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <Link href="/">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">RS Leaders (97 Club)</h1>
        <p className="text-muted-foreground">
          Top 3% relative strength performers with volatility-adjusted scores
        </p>
      </div>

      {/* Screener Info */}
      {screenerInfo && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Date</CardDescription>
              <CardTitle className="text-2xl">{screenerInfo.date}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Stocks</CardDescription>
              <CardTitle className="text-2xl">{screenerInfo.count}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Min RS Percentile</CardDescription>
              <CardTitle className="text-2xl">97%</CardTitle>
            </CardHeader>
          </Card>
        </div>
      )}

      {/* Data Table */}
      <Card>
        <CardHeader>
          <CardTitle>Stock List</CardTitle>
          <CardDescription>
            Sorted by RS percentile. Click column headers to sort.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-muted-foreground">Loading data...</div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-destructive">Error: {error}</div>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={data}
              searchKey="symbol"
              searchPlaceholder="Search by symbol..."
              showMarketCapFilter={true}
            />
          )}
        </CardContent>
      </Card>

      {/* Legend */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Metrics Explained</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <div>
            <strong>RS %ile:</strong> Relative Strength Percentile (0-100%) - Ranks stock
            performance vs universe based on 1-month change
          </div>
          <div>
            <strong>VARS:</strong> Volatility-Adjusted Relative Strength = RS / ADR% - Higher
            is better
          </div>
          <div>
            <strong>1M/1W Change:</strong> Price change over 1 month/1 week
          </div>
          <div>
            <strong>Stage:</strong> Weinstein Stage Analysis (1=Accumulation, 2A/2B/2C=Markup,
            3=Distribution, 4=Decline)
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
