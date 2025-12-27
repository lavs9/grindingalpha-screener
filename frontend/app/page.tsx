import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TrendingUp, TrendingDown, Activity, BarChart3, Target, Layers, Zap, PieChart, Building2, GitCompare, Gauge, GitMerge, Expand, Compass } from 'lucide-react';

const screeners = [
  {
    id: 'breakouts',
    name: '4% Daily Breakouts',
    description: 'Stocks with momentum surge and volume confirmation',
    icon: TrendingUp,
    href: '/screeners/breakouts',
    color: 'text-green-600',
  },
  {
    id: 'rs-leaders',
    name: 'RS Leaders (97 Club)',
    description: 'Top 3% relative strength performers',
    icon: Target,
    href: '/screeners/rs-leaders',
    color: 'text-blue-600',
  },
  {
    id: 'high-volume',
    name: 'High Volume Movers',
    description: 'Extreme volume with price action',
    icon: Activity,
    href: '/screeners/high-volume',
    color: 'text-purple-600',
  },
  {
    id: 'ma-stacked',
    name: 'MA Stacked Breakouts',
    description: 'Perfect moving average alignment (VCP patterns)',
    icon: Layers,
    href: '/screeners/ma-stacked',
    color: 'text-indigo-600',
  },
  {
    id: 'weekly-movers',
    name: '20% Weekly Movers',
    description: 'Extreme weekly swings for patterns',
    icon: TrendingDown,
    href: '/screeners/weekly-movers',
    color: 'text-orange-600',
  },
  {
    id: 'stage-analysis',
    name: 'Stage Analysis',
    description: 'Market structure breakdown (Weinstein stages)',
    icon: BarChart3,
    href: '/screeners/stage-analysis',
    color: 'text-cyan-600',
  },
  {
    id: 'momentum',
    name: 'Momentum Watchlist',
    description: 'High RS stocks holding above SMA50',
    icon: Zap,
    href: '/screeners/momentum',
    color: 'text-yellow-600',
  },
  {
    id: 'breadth',
    name: 'Market Breadth',
    description: 'Universe-wide health metrics',
    icon: PieChart,
    href: '/screeners/breadth',
    color: 'text-pink-600',
  },
  {
    id: 'industries',
    name: 'Leading Industries',
    description: 'Top 20% sectors by strength',
    icon: Building2,
    href: '/screeners/leading-industries',
    color: 'text-emerald-600',
  },
  {
    id: 'rrg',
    name: 'RRG Charts',
    description: 'Sector rotation analysis (120 indices)',
    icon: GitCompare,
    href: '/screeners/rrg',
    color: 'text-violet-600',
  },
  {
    id: 'rsi',
    name: 'RSI Scanner',
    description: 'Overbought/oversold using 14-period RSI',
    icon: Gauge,
    href: '/screeners/rsi-scanner',
    color: 'text-red-600',
  },
  {
    id: 'macd',
    name: 'MACD Crossover',
    description: 'Momentum shifts using MACD (12,26,9)',
    icon: GitMerge,
    href: '/screeners/macd-crossover',
    color: 'text-teal-600',
  },
  {
    id: 'bollinger',
    name: 'Bollinger Squeeze',
    description: 'Low volatility setups before breakouts',
    icon: Expand,
    href: '/screeners/bollinger-squeeze',
    color: 'text-amber-600',
  },
  {
    id: 'adx',
    name: 'ADX Trend Strength',
    description: 'Strong trending stocks using ADX (14)',
    icon: Compass,
    href: '/screeners/adx-trend',
    color: 'text-sky-600',
  },
];

export default function HomePage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Grinding Alpha Screener</h1>
        <p className="text-muted-foreground text-lg">
          Advanced Indian stock market screening with 14 momentum-based strategies
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {screeners.map((screener) => {
          const Icon = screener.icon;
          return (
            <Card key={screener.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-1">{screener.name}</CardTitle>
                    <CardDescription className="text-sm">
                      {screener.description}
                    </CardDescription>
                  </div>
                  <Icon className={`h-6 w-6 ${screener.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <Link href={screener.href}>
                  <Button variant="outline" className="w-full">
                    View Screener
                  </Button>
                </Link>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-12 p-6 border rounded-lg bg-muted/30">
        <h2 className="text-xl font-semibold mb-2">About This Dashboard</h2>
        <p className="text-muted-foreground mb-4">
          This screener platform analyzes <strong>1,691 NSE securities</strong> and <strong>121 sectoral indices</strong> with 64 technical indicators including RS percentile, VARS, Stage Analysis, VCP patterns, McClellan Oscillator, RSI, MACD, Bollinger Bands, and ADX.
        </p>
        <p className="text-sm text-muted-foreground">
          Data updated daily • Backend: FastAPI + PostgreSQL • Frontend: Next.js + Shadcn/ui
        </p>
      </div>
    </div>
  );
}
