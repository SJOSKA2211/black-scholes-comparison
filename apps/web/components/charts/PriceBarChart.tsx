"use client";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ReferenceLine,
} from "recharts";

interface PriceBarChartProps {
  data: { method: string; price: number }[];
  analyticalPrice?: number;
}

export function PriceBarChart({ data, analyticalPrice }: PriceBarChartProps) {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#1e293b"
            vertical={false}
          />
          <XAxis
            dataKey="method"
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="#64748b"
            fontSize={12}
            tickLine={false}
            axisLine={false}
            domain={["auto", "auto"]}
          />
          <Tooltip
            cursor={{ fill: "#1e293b", opacity: 0.4 }}
            contentStyle={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "12px",
            }}
            itemStyle={{ color: "#fff", fontWeight: "bold" }}
          />
          {analyticalPrice && (
            <ReferenceLine
              y={analyticalPrice}
              stroke="#2563eb"
              strokeDasharray="5 5"
              label={{
                position: "right",
                value: "Analytical",
                fill: "#2563eb",
                fontSize: 10,
              }}
            />
          )}
          <Bar dataKey="price" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.method === "Analytical" ? "#2563eb" : "#334155"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
