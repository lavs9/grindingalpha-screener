"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchADXTrend } from "@/lib/api/screeners";
import type { ADXStock, ScreenerResponse } from "@/lib/types/screener";
import { formatMarketCap } from "@/lib/utils";

// Column definitions for ADX Trend Strength table
const columns: ColumnDef<ADXStock>[] = [
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
    accessorKey: "adx_14",
    header: ({ column }) => <SortableHeader column={column}>ADX (14)</SortableHeader>,
    cell: ({ row }) => {
      const adx = row.getValue("adx_14") as number;
      let colorClass = "";
      if (adx > 50) colorClass = "text-purple-600 font-bold";
      else if (adx > 25) colorClass = "text-blue-600 font-bold";
      return <div className={`font-mono text-sm ${colorClass}`}>{adx.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "is_strong_trend",
    header: "Strong Trend",
    cell: ({ row }) => {
      const isStrong = row.getValue("is_strong_trend") as boolean;
      return isStrong ? (
        <Badge className="bg-blue-600">Yes</Badge>
      ) : (
        <span className="text-muted-foreground">—</span>
      );
    },
  },
  {
    accessorKey: "trend_direction",
    header: "Direction",
    cell: ({ row }) => {
      const direction = row.getValue("trend_direction") as string;
      if (direction === "Bullish") return <Badge className="bg-green-600">Bullish</Badge>;
      if (direction === "Bearish") return <Badge variant="destructive">Bearish</Badge>;
      return <Badge variant="outline">Neutral</Badge>;
    },
  },
  {
    accessorKey: "di_plus",
    header: ({ column }) => <SortableHeader column={column}>+DI</SortableHeader>,
    cell: ({ row }) => {
      const value = row.getValue("di_plus") as number;
      return <div className="font-mono text-sm text-green-600">{value.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "di_minus",
    header: ({ column }) => <SortableHeader column={column}>-DI</SortableHeader>,
    cell: ({ row }) => {
      const value = row.getValue("di_minus") as number;
      return <div className="font-mono text-sm text-red-600">{value.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "close",
    header: ({ column }) => <SortableHeader column={column}>Price</SortableHeader>,
    cell: ({ row }) => {
      const close = row.getValue("close") as number;
      return <div className="font-mono">₹{close.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "change_1m_percent",
    header: ({ column }) => <SortableHeader column={column}>1M %</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1m_percent") as number | null;
      if (change === null) return <span className="text-muted-foreground">—</span>;
      const colorClass = change >= 0 ? "text-green-600" : "text-red-600";
      return (
        <div className={`font-mono text-sm ${colorClass}`}>
          {change >= 0 ? "+" : ""}
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
];

export default function ADXTrendPage() {
  const [data, setData] = React.useState<ScreenerResponse<ADXStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchADXTrend({ limit: 200 });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading ADX trend:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-muted-foreground">Loading ADX trend strength...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-destructive">Error: {error}</div>
        </div>
      </div>
    );
  }

  if (!data || data.results.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardHeader>
            <CardTitle>ADX Trend Strength Scanner</CardTitle>
            <CardDescription>
              Identify strong trends using Average Directional Index
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-muted-foreground">
              No data available for the selected date.
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>ADX Trend Strength Scanner</CardTitle>
          <CardDescription>
            Measure trend strength using 14-period ADX (Average Directional Index) •{" "}
            {data.total_results} stocks • Data as of {data.date}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={data.results}
            searchKey="symbol"
            searchPlaceholder="Search symbol..."
            showMarketCapFilter={true}
          />
        </CardContent>
      </Card>

      {/* Legend */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">ADX Interpretation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <Badge className="bg-blue-600 mb-2">Strong Trend (ADX &gt; 25)</Badge>
              <p className="text-muted-foreground">
                Clear directional movement - trend is strong enough to trade
              </p>
            </div>
            <div>
              <Badge className="bg-purple-600 mb-2">Very Strong Trend (ADX &gt; 50)</Badge>
              <p className="text-muted-foreground">
                Extremely strong trend - high conviction directional move
              </p>
            </div>
            <div>
              <Badge className="bg-green-600 mb-2">Bullish (+DI &gt; -DI)</Badge>
              <p className="text-muted-foreground">
                Plus Directional Indicator above Minus DI - upward trend
              </p>
            </div>
            <div>
              <Badge variant="destructive" className="mb-2">Bearish (-DI &gt; +DI)</Badge>
              <p className="text-muted-foreground">
                Minus Directional Indicator above Plus DI - downward trend
              </p>
            </div>
            <div className="col-span-2">
              <p className="text-muted-foreground">
                <strong>Weak Trend (ADX &lt; 25):</strong> Sideways or choppy movement - trend not established yet
              </p>
              <p className="text-muted-foreground mt-2">
                <strong>Calculation:</strong> ADX measures trend strength (0-100), +DI measures upward pressure, -DI measures downward pressure. All use 14-period smoothing.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
