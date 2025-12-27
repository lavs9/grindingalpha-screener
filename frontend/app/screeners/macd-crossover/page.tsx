"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchMACDCrossover } from "@/lib/api/screeners";
import type { MACDStock, ScreenerResponse } from "@/lib/types/screener";
import { formatMarketCap } from "@/lib/utils";

// Column definitions for MACD Crossover table
const columns: ColumnDef<MACDStock>[] = [
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
    accessorKey: "crossover_type",
    header: "Crossover",
    cell: ({ row }) => {
      const type = row.getValue("crossover_type") as string;
      if (type === "Bullish") return <Badge className="bg-green-600">Bullish</Badge>;
      if (type === "Bearish") return <Badge variant="destructive">Bearish</Badge>;
      return <span className="text-muted-foreground">—</span>;
    },
  },
  {
    accessorKey: "macd_histogram",
    header: ({ column }) => <SortableHeader column={column}>Histogram</SortableHeader>,
    cell: ({ row }) => {
      const histogram = row.getValue("macd_histogram") as number;
      const colorClass = histogram >= 0 ? "text-green-600" : "text-red-600";
      return <div className={`font-mono text-sm ${colorClass}`}>{histogram.toFixed(4)}</div>;
    },
  },
  {
    accessorKey: "macd_line",
    header: ({ column }) => <SortableHeader column={column}>MACD Line</SortableHeader>,
    cell: ({ row }) => {
      const value = row.getValue("macd_line") as number;
      return <div className="font-mono text-sm">{value.toFixed(4)}</div>;
    },
  },
  {
    accessorKey: "macd_signal",
    header: ({ column }) => <SortableHeader column={column}>Signal Line</SortableHeader>,
    cell: ({ row }) => {
      const value = row.getValue("macd_signal") as number;
      return <div className="font-mono text-sm">{value.toFixed(4)}</div>;
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

export default function MACDCrossoverPage() {
  const [data, setData] = React.useState<ScreenerResponse<MACDStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchMACDCrossover({ limit: 200 });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading MACD crossover:", err);
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
          <div className="text-lg text-muted-foreground">Loading MACD crossover...</div>
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
            <CardTitle>MACD Crossover Scanner</CardTitle>
            <CardDescription>
              Detect trend and momentum shifts using MACD
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
          <CardTitle>MACD Crossover Scanner</CardTitle>
          <CardDescription>
            Detect trend and momentum shifts using MACD (Moving Average Convergence Divergence) •{" "}
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
          <CardTitle className="text-base">MACD Interpretation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <Badge className="bg-green-600 mb-2">Bullish Crossover</Badge>
              <p className="text-muted-foreground">
                MACD line crosses above signal line - momentum turning positive
              </p>
            </div>
            <div>
              <Badge variant="destructive" className="mb-2">Bearish Crossover</Badge>
              <p className="text-muted-foreground">
                MACD line crosses below signal line - momentum turning negative
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">
                <strong>Positive Histogram:</strong> MACD line above signal (bullish momentum)
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">
                <strong>Negative Histogram:</strong> MACD line below signal (bearish momentum)
              </p>
            </div>
            <div className="col-span-2">
              <p className="text-muted-foreground">
                <strong>Calculation:</strong> MACD Line = 12-EMA - 26-EMA, Signal Line = 9-EMA of MACD Line, Histogram = MACD Line - Signal Line
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
