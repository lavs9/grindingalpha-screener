"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchWeeklyMovers } from "@/lib/api/screeners";
import type { WeeklyMoverStock, ScreenerResponse } from "@/lib/types/screener";

// Column definitions for Weekly Movers table
const columns: ColumnDef<WeeklyMoverStock>[] = [
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
    accessorKey: "change_1w_percent",
    header: ({ column }) => <SortableHeader column={column}>Weekly %</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1w_percent") as number;
      const isPositive = change >= 0;
      const isExtreme = Math.abs(change) >= 30;
      return (
        <div
          className={`font-mono font-semibold ${
            isPositive ? "text-green-600" : "text-red-600"
          } ${isExtreme ? "text-lg" : ""}`}
        >
          {isPositive ? "+" : ""}
          {change.toFixed(2)}%
        </div>
      );
    },
  },
  {
    accessorKey: "change_1d_percent",
    header: ({ column }) => <SortableHeader column={column}>Daily %</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("change_1d_percent") as number;
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
    accessorKey: "adr_percent",
    header: ({ column }) => <SortableHeader column={column}>ADR %</SortableHeader>,
    cell: ({ row }) => {
      const adr = row.getValue("adr_percent") as number;
      return (
        <div className="font-mono">
          {adr.toFixed(2)}%
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

export default function WeeklyMoversPage() {
  const [data, setData] = React.useState<ScreenerResponse<WeeklyMoverStock> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [minChange, setMinChange] = React.useState<string>("20");
  const [direction, setDirection] = React.useState<'up' | 'down' | 'both'>('both');

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchWeeklyMovers({
          minChange: parseFloat(minChange) || 20.0,
          direction: direction,
        });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading Weekly Movers data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [minChange, direction]);

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center h-96">
          <div className="text-muted-foreground">Loading weekly movers data...</div>
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
  const avgWeeklyChange = data.results.length > 0
    ? data.results.reduce((sum, stock) => sum + Math.abs(stock.change_1w_percent), 0) / data.results.length
    : 0;
  const maxWeeklyChange = data.results.length > 0
    ? Math.max(...data.results.map(s => Math.abs(s.change_1w_percent)))
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
        <h1 className="text-3xl font-bold mb-2">Weekly Movers (20%+)</h1>
        <p className="text-muted-foreground">
          Stocks with extreme weekly price swings for swing trading and pattern recognition
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
            <CardDescription>Avg Weekly Move</CardDescription>
            <CardTitle className="text-xl">{avgWeeklyChange.toFixed(1)}%</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Max Weekly Move</CardDescription>
            <CardTitle className="text-xl">{maxWeeklyChange.toFixed(1)}%</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Filters</CardTitle>
          <CardDescription>
            Customize minimum weekly change and direction
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            {/* Min Change Filter */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Minimum Weekly % Change</label>
              <Input
                type="number"
                step="5"
                min="10"
                max="50"
                value={minChange}
                onChange={(e) => setMinChange(e.target.value)}
                className="w-[180px]"
                placeholder="20"
              />
            </div>

            {/* Direction Filter */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Direction</label>
              <Select value={direction} onValueChange={(value) => setDirection(value as 'up' | 'down' | 'both')}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select direction" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="both">Both (Up & Down)</SelectItem>
                  <SelectItem value="up">Up Only (+)</SelectItem>
                  <SelectItem value="down">Down Only (-)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Info text */}
            <div className="text-sm text-muted-foreground">
              {direction === 'both' ? `±${minChange}%` : direction === 'up' ? `+${minChange}%` : `-${minChange}%`} weekly move or more
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Weekly Movers Table */}
      <Card>
        <CardHeader>
          <CardTitle>Weekly Swing Stocks</CardTitle>
          <CardDescription>
            Stocks with {direction === 'both' ? '±' : direction === 'up' ? '+' : '-'}{minChange}% weekly price movement
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
            <strong>Weekly % Change:</strong> 5-day (1 week) price change. Extreme moves (≥30%) shown in larger text.
            Positive (green) = gains, Negative (red) = losses.
          </div>
          <div>
            <strong>Daily % Change:</strong> Most recent day's price change. Compare with weekly change to identify
            momentum continuation or exhaustion.
          </div>
          <div>
            <strong>ADR % (Average Daily Range):</strong> Average daily price volatility over 20 days.
            Higher ADR = More volatile stock. Use to size positions appropriately.
          </div>
          <div>
            <strong>RVOL (Relative Volume):</strong> Today's volume vs 50-day average.
            <Badge variant="default" className="text-xs ml-1">≥2.0x</Badge> indicates institutional participation
            during the weekly move.
          </div>
          <div>
            <strong>Stage:</strong> Mark Minervini's stage classification:
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><Badge className="bg-green-500 text-xs">Stage 2</Badge> + large up move = Momentum continuation (bullish)</li>
              <li><Badge className="bg-yellow-500 text-xs">Stage 3</Badge> + large down move = Distribution breakdown (bearish)</li>
              <li><Badge className="bg-red-500 text-xs">Stage 4</Badge> + large down move = Downtrend acceleration (avoid)</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Trading Strategies:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Upward Movers (+20%+):</strong> Look for pullbacks to moving averages for continuation entries.
                Avoid chasing if RVOL is low (institutional selling into retail buying).</li>
              <li><strong>Downward Movers (-20%+):</strong> Identify failed breakdowns (Stage 2 stock with large down
                move but high RVOL) for reversal plays. Or use for short sale candidates if Stage 3/4.</li>
              <li><strong>High ADR Stocks:</strong> Wide daily ranges require wider stops and smaller position sizes.
                ADR &gt;5% = Swing trading, ADR &gt;8% = Day trading only.</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Pro Tip:</strong> Cross-reference with 4% Breakouts and High Volume screeners. If a stock appears
            in both Weekly Movers and daily screeners, it shows sustained momentum (not just a one-day spike).
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
