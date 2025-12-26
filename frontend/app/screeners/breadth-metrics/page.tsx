"use client";

import * as React from "react";
import { ArrowLeft, TrendingUp, TrendingDown } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchBreadthMetrics } from "@/lib/api/screeners";
import type { BreadthMetricsResponse } from "@/lib/types/screener";

export default function BreadthMetricsPage() {
  const [data, setData] = React.useState<BreadthMetricsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        const response = await fetchBreadthMetrics();
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
        console.error("Error loading Breadth Metrics data:", err);
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
          <div className="text-muted-foreground">Loading breadth metrics...</div>
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

  // Determine market health based on breadth metrics
  const getMarketHealth = () => {
    const { up_down_ratio } = data.up_down;
    const { above_sma20_percent } = data.ma_analysis;
    const { high_low_ratio } = data.new_highs_lows;
    const { oscillator } = data.mcclellan;

    let bullishSignals = 0;
    if (up_down_ratio > 1.2) bullishSignals++;
    if (above_sma20_percent > 50) bullishSignals++;
    if (high_low_ratio > 1.0) bullishSignals++;
    if (oscillator > 50) bullishSignals++;

    if (bullishSignals >= 3) return { status: "Bullish", color: "text-green-600", bgColor: "bg-green-100" };
    if (bullishSignals <= 1) return { status: "Bearish", color: "text-red-600", bgColor: "bg-red-100" };
    return { status: "Neutral", color: "text-yellow-600", bgColor: "bg-yellow-100" };
  };

  const marketHealth = getMarketHealth();

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
        <h1 className="text-3xl font-bold mb-2">Breadth Metrics Dashboard</h1>
        <p className="text-muted-foreground">
          Market-wide participation metrics for gauging overall market health
        </p>
      </div>

      {/* Market Health Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Overall Market Health</CardTitle>
          <CardDescription>Based on breadth indicators</CardDescription>
        </CardHeader>
        <CardContent>
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg ${marketHealth.bgColor}`}>
            <span className={`text-2xl font-bold ${marketHealth.color}`}>
              {marketHealth.status}
            </span>
            <Badge variant="outline" className="text-xs">
              {data.date}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Up/Down Metrics */}
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Daily Advance/Decline</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Advancing Stocks</CardDescription>
              <CardTitle className="text-3xl text-green-600 flex items-center gap-2">
                <TrendingUp className="w-6 h-6" />
                {data.up_down.up_count}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                {((data.up_down.up_count / data.total_stocks) * 100).toFixed(1)}% of universe
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Declining Stocks</CardDescription>
              <CardTitle className="text-3xl text-red-600 flex items-center gap-2">
                <TrendingDown className="w-6 h-6" />
                {data.up_down.down_count}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                {((data.up_down.down_count / data.total_stocks) * 100).toFixed(1)}% of universe
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Up/Down Ratio</CardDescription>
              <CardTitle className={`text-3xl ${data.up_down.up_down_ratio >= 1 ? 'text-green-600' : 'text-red-600'}`}>
                {data.up_down.up_down_ratio.toFixed(2)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                {data.up_down.up_down_ratio >= 1.5 ? "Strong buying" : data.up_down.up_down_ratio >= 1.0 ? "Bullish bias" : data.up_down.up_down_ratio >= 0.7 ? "Bearish bias" : "Strong selling"}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Moving Average Analysis */}
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">Moving Average Participation</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Above 20 SMA</CardDescription>
              <CardTitle className="text-3xl">
                {data.ma_analysis.above_sma20_count}
                <span className="text-base font-normal text-muted-foreground ml-2">
                  ({data.ma_analysis.above_sma20_percent.toFixed(1)}%)
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                <div
                  className={`h-full ${data.ma_analysis.above_sma20_percent >= 60 ? 'bg-green-500' : data.ma_analysis.above_sma20_percent >= 40 ? 'bg-yellow-500' : 'bg-red-500'} transition-all duration-500`}
                  style={{ width: `${data.ma_analysis.above_sma20_percent}%` }}
                />
              </div>
              <div className="text-sm text-muted-foreground mt-2">
                Short-term trend strength
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Above 200 SMA</CardDescription>
              <CardTitle className="text-3xl">
                {data.ma_analysis.above_sma200_count}
                <span className="text-base font-normal text-muted-foreground ml-2">
                  ({data.ma_analysis.above_sma200_percent.toFixed(1)}%)
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                <div
                  className={`h-full ${data.ma_analysis.above_sma200_percent >= 60 ? 'bg-green-500' : data.ma_analysis.above_sma200_percent >= 40 ? 'bg-yellow-500' : 'bg-red-500'} transition-all duration-500`}
                  style={{ width: `${data.ma_analysis.above_sma200_percent}%` }}
                />
              </div>
              <div className="text-sm text-muted-foreground mt-2">
                Long-term trend strength
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* New Highs/Lows */}
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">New 20-Day Highs/Lows</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>New Highs</CardDescription>
              <CardTitle className="text-3xl text-green-600">
                {data.new_highs_lows.new_20d_highs}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                Stocks at 20-day highs
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>New Lows</CardDescription>
              <CardTitle className="text-3xl text-red-600">
                {data.new_highs_lows.new_20d_lows}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                Stocks at 20-day lows
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>High/Low Ratio</CardDescription>
              <CardTitle className={`text-3xl ${data.new_highs_lows.high_low_ratio >= 1 ? 'text-green-600' : 'text-red-600'}`}>
                {data.new_highs_lows.high_low_ratio.toFixed(2)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                {data.new_highs_lows.high_low_ratio >= 2.0 ? "Very bullish" : data.new_highs_lows.high_low_ratio >= 1.0 ? "Bullish" : data.new_highs_lows.high_low_ratio >= 0.5 ? "Bearish" : "Very bearish"}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* McClellan Oscillator */}
      <div className="mb-6">
        <h2 className="text-xl font-bold mb-4">McClellan Oscillator</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Oscillator Value</CardDescription>
              <CardTitle className={`text-3xl ${data.mcclellan.oscillator > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {data.mcclellan.oscillator > 0 ? '+' : ''}{data.mcclellan.oscillator.toFixed(1)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                {Math.abs(data.mcclellan.oscillator) > 100 ? "Extreme reading" : Math.abs(data.mcclellan.oscillator) > 50 ? "Strong momentum" : "Moderate momentum"}
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Based on {data.mcclellan.universe_up_count} up vs {data.mcclellan.universe_down_count} down
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Summation Index</CardDescription>
              <CardTitle className={`text-3xl ${data.mcclellan.summation > 0 ? 'text-green-600' : 'text-red-600'}`}>
                {data.mcclellan.summation > 0 ? '+' : ''}{data.mcclellan.summation.toFixed(1)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                Cumulative breadth trend
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Legend */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-lg">Breadth Metrics Guide</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-3">
          <div>
            <strong>Up/Down Ratio:</strong> Advancing stocks ÷ Declining stocks.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>&gt;1.5:</strong> Strong buying pressure, bullish confirmation</li>
              <li><strong>1.0-1.5:</strong> Moderate bullish bias</li>
              <li><strong>0.7-1.0:</strong> Moderate bearish bias</li>
              <li><strong>&lt;0.7:</strong> Strong selling pressure, bearish confirmation</li>
            </ul>
          </div>
          <div>
            <strong>MA Participation:</strong> Percentage of stocks above key moving averages.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>&gt;60% above 20 SMA:</strong> Strong short-term uptrend</li>
              <li><strong>&gt;60% above 200 SMA:</strong> Strong long-term bull market</li>
              <li><strong>&lt;40%:</strong> Weak trend, distribution phase</li>
            </ul>
          </div>
          <div>
            <strong>New Highs/Lows:</strong> Stocks making 20-day price extremes.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Ratio &gt;2.0:</strong> Strong leadership, sustainable rally</li>
              <li><strong>Ratio &gt;1.0:</strong> More stocks breaking out than down, bullish</li>
              <li><strong>Ratio &lt;0.5:</strong> More breakdowns, bearish divergence</li>
            </ul>
          </div>
          <div>
            <strong>McClellan Oscillator:</strong> Momentum indicator based on advancing-declining issues.
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>&gt;+100:</strong> Overbought, potential pullback ahead</li>
              <li><strong>0 to +100:</strong> Healthy uptrend momentum</li>
              <li><strong>0 to -100:</strong> Downtrend momentum</li>
              <li><strong>&lt;-100:</strong> Oversold, potential bounce</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Trading Strategy:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li><strong>Bullish Breadth:</strong> 3-4 bullish signals = aggressive long positioning, high conviction</li>
              <li><strong>Neutral Breadth:</strong> 2 bullish signals = selective longs, tight stops</li>
              <li><strong>Bearish Breadth:</strong> 0-1 bullish signals = defensive positioning, raise cash, avoid new longs</li>
            </ul>
          </div>
          <div className="pt-2 border-t">
            <strong>Pro Tip:</strong> Breadth divergences are powerful signals. If market indices make new highs
            but breadth metrics weaken (fewer stocks participating), it signals a fragile rally vulnerable to reversal.
            Always confirm price moves with breadth confirmation.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
