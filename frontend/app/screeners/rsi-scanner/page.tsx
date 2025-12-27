"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchRSIScanner } from "@/lib/api/screeners";
import type { RSIStock, ScreenerResponse } from "@/lib/types/screener";
import { formatMarketCap } from "@/lib/utils";

// Column definitions for RSI Scanner table
const columns: ColumnDef<RSIStock>[] = [
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
    accessorKey: "rsi_14",
    header: ({ column }) => <SortableHeader column={column}>RSI (14)</SortableHeader>,
    cell: ({ row }) => {
      const rsi = row.getValue("rsi_14") as number;
      const colorClass = rsi < 30 ? "text-red-600 font-bold" : rsi > 70 ? "text-green-600 font-bold" : "";
      return <div className={`font-mono text-sm ${colorClass}`}>{rsi.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "is_oversold",
    header: "Oversold",
    cell: ({ row }) => {
      const isOversold = row.getValue("is_oversold") as boolean;
      return isOversold ? (
        <Badge variant="destructive">Yes</Badge>
      ) : (
        <span className="text-muted-foreground">—</span>
      );
    },
  },
  {
    accessorKey: "is_overbought",
    header: "Overbought",
    cell: ({ row }) => {
      const isOverbought = row.getValue("is_overbought") as boolean;
      return isOverbought ? (
        <Badge className="bg-green-600">Yes</Badge>
      ) : (
        <span className="text-muted-foreground">—</span>
      );
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
    accessorKey: "change_1w_percent",
    header: ({ column }) => <SortableHeader column={column}>1W %</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1w_percent") as number | null;
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
    accessorKey: "volume",
    header: ({ column }) => <SortableHeader column={column}>Volume</SortableHeader>,
    cell: ({ row }) => {
      const vol = row.getValue("volume") as number;
      return <div className="font-mono text-sm">{vol.toLocaleString("en-IN")}</div>;
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

export default function RSIScannerPage() {
  const [data, setData] = React.useState<ScreenerResponse<RSIStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchRSIScanner({ limit: 200 });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading RSI scanner:", err);
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
          <div className="text-lg text-muted-foreground">Loading RSI scanner...</div>
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
            <CardTitle>RSI Overbought/Oversold Scanner</CardTitle>
            <CardDescription>
              14-period RSI indicator for potential reversal signals
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
          <CardTitle>RSI Overbought/Oversold Scanner</CardTitle>
          <CardDescription>
            Identify potential reversals using 14-period RSI (Relative Strength Index) •{" "}
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
          <CardTitle className="text-base">RSI Interpretation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <Badge variant="destructive" className="mb-2">Oversold (RSI &lt; 30)</Badge>
              <p className="text-muted-foreground">
                Potential buy signal - stock may be undervalued and due for a bounce
              </p>
            </div>
            <div>
              <Badge className="bg-green-600 mb-2">Overbought (RSI &gt; 70)</Badge>
              <p className="text-muted-foreground">
                Potential sell signal - stock may be overvalued and due for a pullback
              </p>
            </div>
            <div className="col-span-2">
              <p className="text-muted-foreground">
                <strong>Neutral Zone (30-70):</strong> RSI in this range indicates normal trading conditions without extreme overbought or oversold signals.
              </p>
              <p className="text-muted-foreground mt-2">
                <strong>Calculation:</strong> 14-period Wilder's smoothing method. RS = Avg Gain / Avg Loss, RSI = 100 - (100 / (1 + RS))
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
