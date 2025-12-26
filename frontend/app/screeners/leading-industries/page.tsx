"use client";

import * as React from "react";
import { ColumnDef } from "@tanstack/react-table";
import { ArrowLeft, TrendingUp } from "lucide-react";
import Link from "next/link";

import { DataTable, SortableHeader } from "@/components/tables/data-table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchLeadingIndustries } from "@/lib/api/screeners";
import type { LeadingIndustry, ScreenerResponse } from "@/lib/types/screener";
import { formatMarketCap } from "@/lib/utils";

// Column definitions for Leading Industries table
const columns: ColumnDef<LeadingIndustry>[] = [
  {
    accessorKey: "industry",
    header: "Industry",
    cell: ({ row }) => (
      <div className="font-semibold max-w-[200px]">{row.getValue("industry")}</div>
    ),
  },
  {
    accessorKey: "sector",
    header: "Sector",
    cell: ({ row }) => (
      <div className="text-sm text-muted-foreground max-w-[150px] truncate" title={row.getValue("sector")}>
        {row.getValue("sector")}
      </div>
    ),
  },
  {
    accessorKey: "stock_count",
    header: ({ column }) => <SortableHeader column={column}>Stocks</SortableHeader>,
    cell: ({ row }) => {
      const count = row.getValue("stock_count") as number;
      return <div className="font-mono">{count}</div>;
    },
  },
  {
    accessorKey: "avg_vars",
    header: ({ column }) => <SortableHeader column={column}>Avg VARS</SortableHeader>,
    cell: ({ row }) => {
      const vars = row.getValue("avg_vars") as number;
      return (
        <Badge variant={vars >= 20 ? "destructive" : vars >= 15 ? "default" : "secondary"} className="font-mono">
          {vars.toFixed(1)}
        </Badge>
      );
    },
  },
  {
    accessorKey: "avg_varw",
    header: ({ column }) => <SortableHeader column={column}>Avg VARW</SortableHeader>,
    cell: ({ row }) => {
      const varw = row.getValue("avg_varw") as number;
      return (
        <Badge variant={varw >= 10 ? "destructive" : varw >= 7 ? "default" : "secondary"} className="font-mono">
          {varw.toFixed(1)}
        </Badge>
      );
    },
  },
  {
    accessorKey: "avg_monthly_change_percent",
    header: ({ column }) => <SortableHeader column={column}>Monthly %</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("avg_monthly_change_percent") as number;
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
    accessorKey: "avg_weekly_change_percent",
    header: ({ column }) => <SortableHeader column={column}>Weekly %</SortableHeader>,
    cell: ({ row }) => {
      const change = row.getValue("avg_weekly_change_percent") as number;
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
    id: "top_performers",
    header: "Top Performers",
    cell: ({ row }) => {
      const performers = row.original.top_performers;
      if (!performers || performers.length === 0) {
        return <div className="text-muted-foreground text-xs">—</div>;
      }

      return (
        <div className="flex flex-wrap gap-1 max-w-[250px]">
          {performers.slice(0, 3).map((perf, idx) => (
            <Badge key={idx} variant="outline" className="text-xs font-mono">
              {perf.symbol}
            </Badge>
          ))}
          {performers.length > 3 && (
            <span className="text-xs text-muted-foreground">+{performers.length - 3} more</span>
          )}
        </div>
      );
    },
  },
];

export default function LeadingIndustriesPage() {
  const [data, setData] = React.useState<ScreenerResponse<LeadingIndustry> | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [expandedRow, setExpandedRow] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchLeadingIndustries({ limit: 20 });
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading Leading Industries data:", err);
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
          <div className="text-muted-foreground">Loading leading industries...</div>
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
  const avgVars = data.results.length > 0
    ? data.results.reduce((sum, ind) => sum + ind.avg_vars, 0) / data.results.length
    : 0;
  const topIndustry = data.results[0];

  return (
    <div className="container mx-auto py-8 px-4 max-w-[1600px]">
      {/* Header */}
      <div className="mb-6">
        <Link href="/">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Home
          </Button>
        </Link>
        <h1 className="text-3xl font-bold mb-2">Leading Industries & Groups</h1>
        <p className="text-muted-foreground">
          Industry rotation analysis for sector rotation strategies
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
            <CardDescription>Industries Tracked</CardDescription>
            <CardTitle className="text-xl">{data.count}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Avg Industry VARS</CardDescription>
            <CardTitle className="text-xl">{avgVars.toFixed(1)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Leading Industry</CardDescription>
            <CardTitle className="text-lg flex items-center gap-1">
              <TrendingUp className="w-5 h-5 text-green-600" />
              <span className="truncate">{topIndustry?.industry || "—"}</span>
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Leading Industries Table */}
      <Card>
        <CardHeader>
          <CardTitle>Industry Rankings</CardTitle>
          <CardDescription>
            Sorted by average VARS (Volatility Adjusted Relative Strength)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns}
            data={data.results}
            searchKey="industry"
            searchPlaceholder="Search industry..."
          />
        </CardContent>
      </Card>

      {/* Top Performers Detail */}
      {data.results.slice(0, 3).map((industry, idx) => (
        <Card key={idx} className="mt-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Badge variant="outline">#{idx + 1}</Badge>
                  {industry.industry}
                </CardTitle>
                <CardDescription>
                  {industry.sector} • {industry.stock_count} stocks
                </CardDescription>
              </div>
              <div className="text-right">
                <div className="text-sm text-muted-foreground">Monthly Performance</div>
                <div className={`text-2xl font-bold ${industry.avg_monthly_change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {industry.avg_monthly_change_percent >= 0 ? '+' : ''}
                  {industry.avg_monthly_change_percent.toFixed(2)}%
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="text-sm font-medium mb-2">Strength Metrics</div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-muted-foreground">VARS</div>
                  <div className="font-mono font-semibold">{industry.avg_vars.toFixed(1)}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">VARW</div>
                  <div className="font-mono font-semibold">{industry.avg_varw.toFixed(1)}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Weekly %</div>
                  <div className={`font-mono ${industry.avg_weekly_change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {industry.avg_weekly_change_percent >= 0 ? '+' : ''}
                    {industry.avg_weekly_change_percent.toFixed(2)}%
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Stock Count</div>
                  <div className="font-mono font-semibold">{industry.stock_count}</div>
                </div>
              </div>
            </div>
            <div>
              <div className="text-sm font-medium mb-2">Top 4 Performers (Monthly)</div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {industry.top_performers.map((perf, perfIdx) => (
                  <div key={perfIdx} className="border rounded-lg p-3">
                    <div className="font-mono font-semibold text-sm">{perf.symbol}</div>
                    <div className="text-xs text-muted-foreground truncate" title={perf.name}>
                      {perf.name}
                    </div>
                    <div className={`text-lg font-bold mt-1 ${perf.change_1m_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {perf.change_1m_percent >= 0 ? '+' : ''}
                      {perf.change_1m_percent.toFixed(2)}%
                    </div>
                    <div className="text-xs font-mono text-muted-foreground mt-1">
                      {formatMarketCap(perf.market_cap)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Legend */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Industry Rotation Guide</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-3">
          <div>
            <strong>VARS (Volatility Adjusted Relative Strength):</strong> Industry's RS percentile adjusted for volatility.
            Higher VARS = stronger industry with sustainable momentum.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><Badge variant="destructive" className="text-xs">≥20</Badge> - Elite industries, strongest leaders</li>
              <li><Badge variant="default" className="text-xs">15-20</Badge> - Strong industries, good opportunities</li>
              <li><Badge variant="secondary" className="text-xs">&lt;15</Badge> - Weaker industries, avoid new entries</li>
            </ul>
          </div>
          <div>
            <strong>VARW (Weekly VARS):</strong> Short-term industry strength over past week.
            Use to confirm momentum continuation or reversal.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>VARW &gt; VARS:</strong> Accelerating momentum, strongest entries</li>
              <li><strong>VARW ≈ VARS:</strong> Stable trend, safe to follow</li>
              <li><strong>VARW &lt; VARS:</strong> Decelerating, early warning signal</li>
            </ul>
          </div>
          <div>
            <strong>Monthly/Weekly Change:</strong> Average price performance across industry stocks.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Both Positive:</strong> Strong uptrend, high conviction</li>
              <li><strong>Monthly +, Weekly -:</strong> Healthy pullback in uptrend</li>
              <li><strong>Monthly -, Weekly +:</strong> Bounce in downtrend, be cautious</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Rotation Strategy:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Focus on Top 3-5 Industries:</strong> These have the strongest tailwinds. Screen for individual stocks within these industries using other screeners (RS Leaders, MA Stacked, etc.)</li>
              <li><strong>Sector Diversification:</strong> Avoid concentrating in one sector. Spread across multiple leading industries from different sectors.</li>
              <li><strong>Rotation Timing:</strong> When top industries start showing VARW &lt; VARS and negative weekly change, rotate to new emerging leaders.</li>
              <li><strong>Stock Selection:</strong> Within leading industries, pick stocks with individual RS ≥85, Stage 2, and tight LoD for best setups.</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Pro Tip:</strong> Industry rotation often leads price action. If a new industry enters the top 5 with high VARS/VARW,
            identify the strongest stocks in that industry BEFORE they make big moves. Use this screener weekly to catch early rotation shifts.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
