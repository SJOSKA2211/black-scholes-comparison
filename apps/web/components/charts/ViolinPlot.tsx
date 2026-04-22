"use client";
import React from "react";
import { ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip } from "recharts";

interface DistributionChartProps {
  data: { method: string; error: number }[];
}

export function ViolinPlot({ data }: DistributionChartProps) {
  // Recharts can simulate a jittered dot plot for distributions
  const jitteredData = React.useMemo(() => data.map((d, i) => ({
    ...d,
    jitter: (i % 10) / 25 + 0.3, // deterministic jitter
  })), [data]);

  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis 
            dataKey="method" 
            name="Method" 
            stroke="#64748b" 
            fontSize={12}
            allowDuplicatedCategory={false}
          />
          <YAxis 
            dataKey="error" 
            name="MAPE %" 
            stroke="#64748b" 
            fontSize={12}
            unit="%"
          />
          <ZAxis type="number" range={[50, 50]} />
          <Tooltip 
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }}
          />
          <Scatter 
            name="Errors" 
            data={jitteredData} 
            fill="#3b82f6" 
            opacity={0.6}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
