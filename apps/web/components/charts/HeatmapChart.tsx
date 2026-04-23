"use client";
import { motion } from "framer-motion";

interface HeatmapChartProps {
  data: { x: string; y: string; value: number }[];
  xLabels: string[];
  yLabels: string[];
}

export function HeatmapChart({ data, xLabels, yLabels }: HeatmapChartProps) {
  const maxValue = Math.max(...data.map((d) => d.value));

  return (
    <div className="w-full overflow-x-auto pb-4">
      <div
        className="inline-grid gap-1"
        style={{ gridTemplateColumns: `auto repeat(${xLabels.length}, 1fr)` }}
      >
        <div /> {/* Top-left spacer */}
        {xLabels.map((label) => (
          <div
            key={label}
            className="text-[10px] font-bold text-slate-500 text-center uppercase tracking-tighter py-2"
          >
            {label}
          </div>
        ))}
        {yLabels.map((yLabel) => (
          <>
            <div
              key={yLabel}
              className="text-[10px] font-bold text-slate-500 pr-4 flex items-center justify-end uppercase whitespace-nowrap"
            >
              {yLabel}
            </div>
            {xLabels.map((xLabel) => {
              const item = data.find((d) => d.x === xLabel && d.y === yLabel);
              const intensity = item ? item.value / maxValue : 0;
              return (
                <motion.div
                  key={`${xLabel}-${yLabel}`}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{ scale: 1.1, zIndex: 10 }}
                  title={`${yLabel} / ${xLabel}: ${item?.value.toFixed(4)}`}
                  className="w-10 h-10 rounded-md cursor-help border border-slate-900"
                  style={{
                    backgroundColor: `rgba(37, 99, 235, ${0.1 + intensity * 0.9})`,
                  }}
                />
              );
            })}
          </>
        ))}
      </div>
    </div>
  );
}
