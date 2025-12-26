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

  // Fixed axis ranges - quadrants should not move
  // Use a reasonable fixed range that accommodates typical RRG values
  const fixedRange = {
    xMin: 96,
    xMax: 104,
    yMin: 97,
    yMax: 103,
  };

  const layout = {
    title: {
      text: `RRG Chart - Sector Rotation vs ${benchmark}`,
      font: { size: 18 },
    },
    xaxis: {
      title: "JdK RS-Ratio",
      zeroline: false,
      gridcolor: "#e5e7eb",
      range: [fixedRange.xMin, fixedRange.xMax],
    },
    yaxis: {
      title: "JdK RS-Momentum",
      zeroline: false,
      gridcolor: "#e5e7eb",
      range: [fixedRange.yMin, fixedRange.yMax],
    },
    shapes: [
      // Quadrant background shading - fixed positions
      // Leading (top-right)
      {
        type: "rect",
        x0: 100,
        x1: fixedRange.xMax,
        y0: 100,
        y1: fixedRange.yMax,
        fillcolor: "#22c55e",
        opacity: 0.1,
        line: { width: 0 },
        layer: "below",
      },
      // Weakening (bottom-right)
      {
        type: "rect",
        x0: 100,
        x1: fixedRange.xMax,
        y0: fixedRange.yMin,
        y1: 100,
        fillcolor: "#eab308",
        opacity: 0.1,
        line: { width: 0 },
        layer: "below",
      },
      // Lagging (bottom-left)
      {
        type: "rect",
        x0: fixedRange.xMin,
        x1: 100,
        y0: fixedRange.yMin,
        y1: 100,
        fillcolor: "#ef4444",
        opacity: 0.1,
        line: { width: 0 },
        layer: "below",
      },
      // Improving (top-left)
      {
        type: "rect",
        x0: fixedRange.xMin,
        x1: 100,
        y0: 100,
        y1: fixedRange.yMax,
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
        y0: fixedRange.yMin,
        y1: fixedRange.yMax,
        line: {
          color: "#666",
          width: 2,
          dash: "dash",
        },
      },
      // Horizontal line at y=100 (RS-Momentum axis)
      {
        type: "line",
        x0: fixedRange.xMin,
        x1: fixedRange.xMax,
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
      // Quadrant labels - fixed positions
      {
        x: 102.5,
        y: 102,
        text: "Leading",
        showarrow: false,
        font: { size: 14, color: "#22c55e", weight: "bold" },
      },
      {
        x: 102.5,
        y: 98,
        text: "Weakening",
        showarrow: false,
        font: { size: 14, color: "#eab308", weight: "bold" },
      },
      {
        x: 97.5,
        y: 98,
        text: "Lagging",
        showarrow: false,
        font: { size: 14, color: "#ef4444", weight: "bold" },
      },
      {
        x: 97.5,
        y: 102,
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
