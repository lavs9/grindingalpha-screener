"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { RRGChart } from "@/components/charts/rrg-chart";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { fetchRRGCharts } from "@/lib/api/screeners";
import type { RRGSector, RRGChartsResponse } from "@/lib/types/screener";

// Column definitions for sector details table
// Note: We'll add the checkbox column dynamically in the component
const createColumns = (
  selectedIndices: Set<string>,
  toggleIndex: (symbol: string) => void
): ColumnDef<RRGSector>[] => [
  {
    id: "select",
    header: () => <div className="w-10"></div>,
    cell: ({ row }) => {
      const symbol = row.getValue("index_symbol") as string;
      return (
        <input
          type="checkbox"
          checked={selectedIndices.has(symbol)}
          onChange={() => toggleIndex(symbol)}
          className="cursor-pointer w-4 h-4"
        />
      );
    },
  },
  {
    accessorKey: "index_symbol",
    header: ({ column }) => <SortableHeader column={column}>Index</SortableHeader>,
    cell: ({ row }) => (
      <div className="font-mono font-semibold">{row.getValue("index_symbol")}</div>
    ),
  },
  {
    accessorKey: "sector_category",
    header: ({ column }) => <SortableHeader column={column}>Sector</SortableHeader>,
    cell: ({ row }) => {
      const category = row.getValue("sector_category") as string | null;
      return <div className="text-sm">{category || "—"}</div>;
    },
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

// Tail length options by timeframe based on RRG best practices
const TAIL_LENGTH_OPTIONS = {
  daily: [
    { value: "5", label: "5 days" },
    { value: "10", label: "10 days" },
    { value: "15", label: "15 days (Default)" },
    { value: "20", label: "20 days" },
  ],
  weekly: [
    { value: "3", label: "3 weeks" },
    { value: "8", label: "8 weeks" },
    { value: "10", label: "10 weeks" },
    { value: "12", label: "12 weeks (Default)" },
  ],
  monthly: [
    { value: "3", label: "3 months" },
    { value: "6", label: "6 months (Default)" },
    { value: "9", label: "9 months" },
    { value: "12", label: "12 months" },
  ],
};

export default function RRGChartsPage() {
  const [data, setData] = React.useState<RRGChartsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [searchFilter, setSearchFilter] = React.useState<string>("");
  const [selectedIndices, setSelectedIndices] = React.useState<Set<string>>(new Set());
  const [timeframe, setTimeframe] = React.useState<"daily" | "weekly" | "monthly">("daily");
  const [tailLength, setTailLength] = React.useState<string>("15");

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchRRGCharts({
          timeframe,
          tailLength: parseInt(tailLength),
        });
        setData(response);
        // Initialize with all indices selected
        setSelectedIndices(new Set(response.results.map(s => s.index_symbol)));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading RRG Charts:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [timeframe, tailLength]);

  // Filter data based on search input and selection
  const filteredResults = React.useMemo(() => {
    if (!data?.results) return [];

    let results = data.results;

    // Apply search filter
    if (searchFilter) {
      const lowerFilter = searchFilter.toLowerCase();
      results = results.filter((sector) =>
        sector.index_symbol.toLowerCase().includes(lowerFilter)
      );
    }

    // Apply selection filter (only show selected indices on chart)
    results = results.filter((sector) => selectedIndices.has(sector.index_symbol));

    return results;
  }, [data?.results, searchFilter, selectedIndices]);

  // Get all indices that match search filter (for table display)
  const searchFilteredResults = React.useMemo(() => {
    if (!data?.results) return [];
    if (!searchFilter) return data.results;

    const lowerFilter = searchFilter.toLowerCase();
    return data.results.filter((sector) =>
      sector.index_symbol.toLowerCase().includes(lowerFilter)
    );
  }, [data?.results, searchFilter]);

  // Toggle individual index selection
  const toggleIndex = (indexSymbol: string) => {
    setSelectedIndices(prev => {
      const next = new Set(prev);
      if (next.has(indexSymbol)) {
        next.delete(indexSymbol);
      } else {
        next.add(indexSymbol);
      }
      return next;
    });
  };

  // Select/deselect all
  const selectAll = () => {
    if (data?.results) {
      setSelectedIndices(new Set(data.results.map(s => s.index_symbol)));
    }
  };

  const deselectAll = () => {
    setSelectedIndices(new Set());
  };

  // Handle timeframe change - reset tail length to default for new timeframe
  const handleTimeframeChange = (newTimeframe: "daily" | "weekly" | "monthly") => {
    setTimeframe(newTimeframe);
    // Set default tail length based on timeframe
    const defaults = { daily: "15", weekly: "12", monthly: "6" };
    setTailLength(defaults[newTimeframe]);
  };

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
            <CardDescription>Rolling Window</CardDescription>
            <CardTitle className="text-xl">{data.short_period} days</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Timeframe and Tail Length Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">Chart Settings</CardTitle>
          <CardDescription>
            Customize the timeframe and tail length for the RRG chart
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            {/* Timeframe Selector */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Timeframe</label>
              <Select value={timeframe} onValueChange={handleTimeframeChange}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Select timeframe" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="daily">Daily</SelectItem>
                  <SelectItem value="weekly">Weekly</SelectItem>
                  <SelectItem value="monthly">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Tail Length Selector */}
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium">Tail Length</label>
              <Select value={tailLength} onValueChange={setTailLength}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Select tail length" />
                </SelectTrigger>
                <SelectContent>
                  {TAIL_LENGTH_OPTIONS[timeframe].map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Info text */}
            <div className="text-sm text-muted-foreground">
              {timeframe === "daily" && "Daily RRGs commonly use 15-day tails"}
              {timeframe === "weekly" && "Weekly RRGs commonly use 12-week tails"}
              {timeframe === "monthly" && "Monthly RRGs commonly use 6-month tails"}
            </div>
          </div>
        </CardContent>
      </Card>

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
            Sectors in the top-right (Leading) quadrant are outperforming with positive momentum.
            {` Displaying ${filteredResults.length} of ${selectedIndices.size} selected indices.`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <RRGChart data={filteredResults} benchmark={data.benchmark} />
        </CardContent>
      </Card>

      {/* Sector Details Table */}
      <Card>
        <CardHeader>
          <CardTitle>Sector Details</CardTitle>
          <CardDescription>
            Select indices to display on the chart. {selectedIndices.size} of {data.count} selected.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Search and Selection Controls */}
            <div className="flex items-center justify-between gap-4">
              <Input
                placeholder="Search index..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="max-w-sm"
              />
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={selectAll}>
                  Select All
                </Button>
                <Button variant="outline" size="sm" onClick={deselectAll}>
                  Deselect All
                </Button>
              </div>
            </div>
            {/* Table with checkboxes */}
            <DataTable
              columns={createColumns(selectedIndices, toggleIndex)}
              data={searchFilteredResults}
            />
          </div>
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
              <strong>Top-Right:</strong> RS-Ratio &gt; 100, RS-Momentum &gt; 100. Sectors
              outperforming the benchmark with increasing strength. <strong>Buy/Hold</strong>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Badge className="bg-yellow-500 mt-0.5">Weakening</Badge>
            <div>
              <strong>Bottom-Right:</strong> RS-Ratio &gt; 100, RS-Momentum ≤ 100. Sectors still
              outperforming but losing momentum. <strong>Take profits</strong>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Badge className="bg-red-500 mt-0.5">Lagging</Badge>
            <div>
              <strong>Bottom-Left:</strong> RS-Ratio ≤ 100, RS-Momentum ≤ 100. Sectors
              underperforming with negative momentum. <strong>Avoid</strong>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <Badge className="bg-blue-500 mt-0.5">Improving</Badge>
            <div>
              <strong>Top-Left:</strong> RS-Ratio ≤ 100, RS-Momentum &gt; 100. Sectors still
              underperforming but gaining momentum. <strong>Watch/Early entry</strong>
            </div>
          </div>
          <div className="pt-2 border-t">
            <strong>JdK RS-Ratio:</strong> 100 + Z-score((Index/Benchmark × 100) over 14-day rolling window).
            Values hover around 100; above 100 = outperforming.
            <br />
            <strong>JdK RS-Momentum:</strong> 101 + Z-score(Rate-of-change of RS-Ratio over 14-day rolling window).
            Values hover around 101; above 101 = gaining strength.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
