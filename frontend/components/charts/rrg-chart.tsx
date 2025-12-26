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
  // Group data by quadrant
  const quadrants = {
    Leading: data.filter((s) => s.quadrant === "Leading"),
    Weakening: data.filter((s) => s.quadrant === "Weakening"),
    Lagging: data.filter((s) => s.quadrant === "Lagging"),
    Improving: data.filter((s) => s.quadrant === "Improving"),
  };

  // Create traces for each quadrant
  const traces = [
    {
      x: quadrants.Leading.map((s) => s.rs_ratio),
      y: quadrants.Leading.map((s) => s.rs_momentum),
      text: quadrants.Leading.map((s) => s.index_symbol),
      mode: "markers+text",
      type: "scatter",
      name: "Leading",
      marker: {
        size: 12,
        color: "#22c55e", // green-500
        symbol: "circle",
      },
      textposition: "top center",
      textfont: { size: 9 },
    },
    {
      x: quadrants.Weakening.map((s) => s.rs_ratio),
      y: quadrants.Weakening.map((s) => s.rs_momentum),
      text: quadrants.Weakening.map((s) => s.index_symbol),
      mode: "markers+text",
      type: "scatter",
      name: "Weakening",
      marker: {
        size: 12,
        color: "#eab308", // yellow-500
        symbol: "circle",
      },
      textposition: "top center",
      textfont: { size: 9 },
    },
    {
      x: quadrants.Lagging.map((s) => s.rs_ratio),
      y: quadrants.Lagging.map((s) => s.rs_momentum),
      text: quadrants.Lagging.map((s) => s.index_symbol),
      mode: "markers+text",
      type: "scatter",
      name: "Lagging",
      marker: {
        size: 12,
        color: "#ef4444", // red-500
        symbol: "circle",
      },
      textposition: "top center",
      textfont: { size: 9 },
    },
    {
      x: quadrants.Improving.map((s) => s.rs_ratio),
      y: quadrants.Improving.map((s) => s.rs_momentum),
      text: quadrants.Improving.map((s) => s.index_symbol),
      mode: "markers+text",
      type: "scatter",
      name: "Improving",
      marker: {
        size: 12,
        color: "#3b82f6", // blue-500
        symbol: "circle",
      },
      textposition: "top center",
      textfont: { size: 9 },
    },
  ];

  const layout = {
    title: {
      text: `RRG Chart - Sector Rotation vs ${benchmark}`,
      font: { size: 18 },
    },
    xaxis: {
      title: "RS-Ratio (Relative Strength)",
      zeroline: true,
      zerolinecolor: "#666",
      zerolinewidth: 2,
      gridcolor: "#e5e7eb",
    },
    yaxis: {
      title: "RS-Momentum (Rate of Change)",
      zeroline: true,
      zerolinecolor: "#666",
      zerolinewidth: 2,
      gridcolor: "#e5e7eb",
    },
    shapes: [
      // Vertical line at x=100
      {
        type: "line",
        x0: 100,
        y0: -10,
        x1: 100,
        y1: 10,
        line: {
          color: "#666",
          width: 2,
          dash: "dash",
        },
      },
      // Horizontal line at y=0
      {
        type: "line",
        x0: 90,
        y0: 0,
        x1: 110,
        y1: 0,
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
        x: 102,
        y: 5,
        text: "Leading",
        showarrow: false,
        font: { size: 14, color: "#22c55e", weight: "bold" },
      },
      {
        x: 102,
        y: -5,
        text: "Weakening",
        showarrow: false,
        font: { size: 14, color: "#eab308", weight: "bold" },
      },
      {
        x: 98,
        y: -5,
        text: "Lagging",
        showarrow: false,
        font: { size: 14, color: "#ef4444", weight: "bold" },
      },
      {
        x: 98,
        y: 5,
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
