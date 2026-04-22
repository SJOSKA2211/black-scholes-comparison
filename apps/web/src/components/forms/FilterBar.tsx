"use client";

import React from "react";
import { Search, Filter, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface FilterBarProps {
  onSearch: (value: string) => void;
  onFilterChange: (key: string, value: string) => void;
  filters: Record<string, string>;
  options?: Record<string, { label: string; value: string }[]>;
}

/**
 * Common Filter Bar for experiments and market data.
 */
export function FilterBar({
  onSearch,
  onFilterChange,
  filters,
  options = {},
}: FilterBarProps) {
  const hasActiveFilters = Object.values(filters).some((v) => v !== "");

  const clearFilters = () => {
    Object.keys(filters).forEach((key) => onFilterChange(key, ""));
    onSearch("");
  };

  return (
    <div className="flex flex-wrap items-center gap-3 p-4 bg-card border rounded-lg shadow-sm">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search..."
          className="pl-9 bg-background/50"
          onChange={(e) => onSearch(e.target.value)}
        />
      </div>

      {Object.entries(options).map(([key, opts]) => (
        <Select
          key={key}
          value={filters[key]}
          onValueChange={(val) => onFilterChange(key, val)}
        >
          <SelectTrigger className="w-[160px] bg-background/50">
            <SelectValue placeholder={`Filter by ${key}`} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All {key}s</SelectItem>
            {opts.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ))}

      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={clearFilters}
          className="text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4 mr-2" />
          Clear
        </Button>
      )}

      <Button variant="outline" size="sm" className="ml-auto">
        <Filter className="h-4 w-4 mr-2" />
        More Filters
      </Button>
    </div>
  );
}
