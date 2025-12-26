"use client";

import * as React from "react";
import dynamic from "next/dynamic";
import type { RRGSector } from "@/lib/types/screener";

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface RRGChartProps {
  data: RRGSector[];
  benchmark: string;
}

export function RRGChart({ data, benchmark }: RRGChartProps) {
  // Handle empty data
  if (!data || data.length === 0) {
    return (
      <div className="w-full h-[600px] flex items-center justify-center text-muted-foreground">
        No data to display. Try adjusting your filters.
      </div>
    );
  }

  // Color mapping by current quadrant
  const quadrantColors = {
    Leading: "#22c55e", // green-500
    Weakening: "#eab308", // yellow-500
    Lagging: "#ef4444", // red-500
    Improving: "#3b82f6", // blue-500
  };

  // Create a trace for each sector (line + marker)
  const traces = data.flatMap((sector) => {
    const color = quadrantColors[sector.quadrant];

    // Extract x and y coordinates from historical_points
    const xValues = sector.historical_points.map((point) => point.rs_ratio);
    const yValues = sector.historical_points.map((point) => point.rs_momentum);

    return [
      // Tail line trace
      {
        x: xValues,
        y: yValues,
        mode: "lines",
        type: "scatter",
        name: sector.index_symbol,
        line: {
          color: color,
          width: 2,
        },
        showlegend: false,
        hoverinfo: "skip",
      },
      // Current position marker trace
      {
        x: [xValues[xValues.length - 1]],
        y: [yValues[yValues.length - 1]],
        mode: "markers+text",
        type: "scatter",
        name: sector.index_symbol,
        marker: {
          size: 10,
          color: color,
          symbol: "circle",
          line: {
            color: "#fff",
            width: 2,
          },
        },
        text: [sector.index_symbol],
        textposition: "top center",
        textfont: { size: 8, color: color },
        hovertemplate:
          `<b>${sector.index_symbol}</b><br>` +
          `RS-Ratio: %{x:.2f}<br>` +
          `RS-Momentum: %{y:.2f}<br>` +
          `Quadrant: ${sector.quadrant}<br>` +
          `Weekly Change: ${sector.weekly_change_percent.toFixed(2)}%<br>` +
          `<extra></extra>`,
        showlegend: true,
        legendgroup: sector.quadrant,
      },
    ];
  });

  // Calculate axis ranges dynamically
  const allRsRatios = data.flatMap(s => s.historical_points.map(p => p.rs_ratio));
  const allRsMomentums = data.flatMap(s => s.historical_points.map(p => p.rs_momentum));

  const minRatio = Math.min(...allRsRatios);
  const maxRatio = Math.max(...allRsRatios);
  const minMomentum = Math.min(...allRsMomentums);
  const maxMomentum = Math.max(...allRsMomentums);

  const layout = {
    title: {
      text: `RRG Chart - Sector Rotation vs ${benchmark}`,
      font: { size: 18 },
    },
    xaxis: {
      title: "JdK RS-Ratio",
      zeroline: false,
      gridcolor: "#e5e7eb",
      range: [Math.floor(minRatio - 1), Math.ceil(maxRatio + 1)],
    },
    yaxis: {
      title: "JdK RS-Momentum",
      zeroline: false,
      gridcolor: "#e5e7eb",
      range: [Math.floor(minMomentum - 1), Math.ceil(maxMomentum + 1)],
    },
    shapes: [
      // Quadrant background shading
      {
        type: "rect",
        x0: 100,
        x1: Math.ceil(maxRatio + 1),
        y0: 100,
        y1: Math.ceil(maxMomentum + 1),
        fillcolor: "#22c55e",
        opacity: 0.1,
        line: { width: 0 },
        layer: "below",
      },
      {
        type: "rect",
        x0: 100,
        x1: Math.ceil(maxRatio + 1),
        y0: Math.floor(minMomentum - 1),
        y1: 100,
        fillcolor: "#eab308",
        opacity: 0.1,
        line: { width: 0 },
        layer: "below",
      },
      {
        type: "rect",
        x0: Math.floor(minRatio - 1),
        x1: 100,
        y0: Math.floor(minMomentum - 1),
        y1: 100,
        fillcolor: "#ef4444",
        opacity: 0.1,
        line: { width: 0 },
        layer: "below",
      },
      {
        type: "rect",
        x0: Math.floor(minRatio - 1),
        x1: 100,
        y0: 100,
        y1: Math.ceil(maxMomentum + 1),
        fillcolor: "#3b82f6",
        opacity: 0.1,
        line: { width: 0 },
        layer: "below",
      },
      // Vertical line at x=100 (RS-Ratio axis)
      {
        type: "line",
        x0: 100,
        x1: 100,
        y0: Math.floor(minMomentum - 1),
        y1: Math.ceil(maxMomentum + 1),
        line: {
          color: "#666",
          width: 2,
          dash: "dash",
        },
      },
      // Horizontal line at y=100 (RS-Momentum axis)
      {
        type: "line",
        x0: Math.floor(minRatio - 1),
        x1: Math.ceil(maxRatio + 1),
        y0: 100,
        y1: 100,
        line: {
          color: "#666",
          width: 2,
          dash: "dash",
        },
      },
    ],
    annotations: [
      // Quadrant labels
      {
        x: 100 + (maxRatio - 100) * 0.7,
        y: 100 + (maxMomentum - 100) * 0.8,
        text: "Leading",
        showarrow: false,
        font: { size: 14, color: "#22c55e", weight: "bold" },
      },
      {
        x: 100 + (maxRatio - 100) * 0.7,
        y: 100 - (100 - minMomentum) * 0.8,
        text: "Weakening",
        showarrow: false,
        font: { size: 14, color: "#eab308", weight: "bold" },
      },
      {
        x: 100 - (100 - minRatio) * 0.7,
        y: 100 - (100 - minMomentum) * 0.8,
        text: "Lagging",
        showarrow: false,
        font: { size: 14, color: "#ef4444", weight: "bold" },
      },
      {
        x: 100 - (100 - minRatio) * 0.7,
        y: 100 + (maxMomentum - 100) * 0.8,
        text: "Improving",
        showarrow: false,
        font: { size: 14, color: "#3b82f6", weight: "bold" },
      },
    ],
    hovermode: "closest",
    showlegend: true,
    legend: {
      x: 1.05,
      y: 1,
    },
    height: 600,
    autosize: true,
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d"],
  };

  return (
    <div className="w-full">
      <Plot data={traces as any} layout={layout as any} config={config} className="w-full" />
    </div>
  );
}
