"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchBollingerSqueeze } from "@/lib/api/screeners";
import type { BollingerStock, ScreenerResponse } from "@/lib/types/screener";
import { formatMarketCap } from "@/lib/utils";

// Column definitions for Bollinger Band Squeeze table
const columns: ColumnDef<BollingerStock>[] = [
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
    accessorKey: "bb_bandwidth_percent",
    header: ({ column }) => <SortableHeader column={column}>Bandwidth %</SortableHeader>,
    cell: ({ row }) => {
      const bandwidth = row.getValue("bb_bandwidth_percent") as number;
      const colorClass = bandwidth < 10 ? "text-orange-600 font-bold" : "";
      return <div className={`font-mono text-sm ${colorClass}`}>{bandwidth.toFixed(2)}%</div>;
    },
  },
  {
    accessorKey: "is_squeeze",
    header: "Squeeze",
    cell: ({ row }) => {
      const isSqueeze = row.getValue("is_squeeze") as boolean;
      return isSqueeze ? (
        <Badge className="bg-orange-600">Yes</Badge>
      ) : (
        <span className="text-muted-foreground">—</span>
      );
    },
  },
  {
    accessorKey: "breakout_direction",
    header: "Breakout",
    cell: ({ row }) => {
      const direction = row.getValue("breakout_direction") as string;
      if (direction === "Above Upper") return <Badge className="bg-green-600">Above Upper</Badge>;
      if (direction === "Below Lower") return <Badge variant="destructive">Below Lower</Badge>;
      return <span className="text-muted-foreground">Within Bands</span>;
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
    accessorKey: "bb_upper",
    header: ({ column }) => <SortableHeader column={column}>Upper Band</SortableHeader>,
    cell: ({ row }) => {
      const value = row.getValue("bb_upper") as number;
      return <div className="font-mono text-sm">₹{value.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "bb_middle",
    header: ({ column }) => <SortableHeader column={column}>Middle (SMA)</SortableHeader>,
    cell: ({ row }) => {
      const value = row.getValue("bb_middle") as number;
      return <div className="font-mono text-sm">₹{value.toFixed(2)}</div>;
    },
  },
  {
    accessorKey: "bb_lower",
    header: ({ column }) => <SortableHeader column={column}>Lower Band</SortableHeader>,
    cell: ({ row }) => {
      const value = row.getValue("bb_lower") as number;
      return <div className="font-mono text-sm">₹{value.toFixed(2)}</div>;
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

export default function BollingerSqueezePage() {
  const [data, setData] = React.useState<ScreenerResponse<BollingerStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchBollingerSqueeze({ limit: 200 });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading Bollinger squeeze:", err);
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
          <div className="text-lg text-muted-foreground">Loading Bollinger squeeze...</div>
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
            <CardTitle>Bollinger Band Squeeze Scanner</CardTitle>
            <CardDescription>
              Identify low-volatility setups before potential breakouts
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
          <CardTitle>Bollinger Band Squeeze Scanner</CardTitle>
          <CardDescription>
            Detect volatility contractions using Bollinger Bands (20, 2) •{" "}
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
          <CardTitle className="text-base">Bollinger Band Interpretation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <Badge className="bg-orange-600 mb-2">Squeeze (Bandwidth &lt; 10%)</Badge>
              <p className="text-muted-foreground">
                Low volatility contraction - potential breakout setup (direction uncertain)
              </p>
            </div>
            <div>
              <Badge className="bg-green-600 mb-2">Above Upper Band</Badge>
              <p className="text-muted-foreground">
                Price breaking out above upper band - potential continuation or overbought
              </p>
            </div>
            <div>
              <Badge variant="destructive" className="mb-2">Below Lower Band</Badge>
              <p className="text-muted-foreground">
                Price breaking down below lower band - potential weakness or oversold
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">
                <strong>Within Bands:</strong> Normal trading range - no extreme volatility
              </p>
            </div>
            <div className="col-span-2">
              <p className="text-muted-foreground">
                <strong>Calculation:</strong> Upper Band = 20-SMA + 2*Std Dev, Middle Band = 20-SMA, Lower Band = 20-SMA - 2*Std Dev, Bandwidth = (Upper - Lower) / Middle * 100
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
