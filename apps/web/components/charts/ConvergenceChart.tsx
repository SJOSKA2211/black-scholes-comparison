"use client";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

interface ConvergenceChartProps {
  data: { steps: number; error: number }[];
}

export function ConvergenceChart({ data }: ConvergenceChartProps) {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis 
            dataKey="steps" 
            scale="log" 
            domain={['auto', 'auto']} 
            type="number"
            stroke="#64748b"
            fontSize={12}
          />
          <YAxis 
            scale="log" 
            domain={['auto', 'auto']} 
            type="number"
            stroke="#64748b"
            fontSize={12}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="error" 
            stroke="#3b82f6" 
            strokeWidth={2} 
            dot={{ r: 4, fill: '#3b82f6' }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
