"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { LineChart } from "recharts";// Assume a LineChart component exists
import { Skeleton } from "../ui/skeleton";

interface TimeSeriesPoint {
  timestamp: string;
  value: number;
}

interface TimeSeriesData {
  points: TimeSeriesPoint[];
}

const fetchTimeSeries = async (): Promise<TimeSeriesData> => {
  const response = await fetch("/api/dashboard/timeseries");
  if (!response.ok) throw new Error("Failed to fetch time series data");
  return response.json();
};

export default function TimeSeriesAnalysis() {
  const queryResult = useQuery<TimeSeriesData, Error>({
    queryKey: ["dashboardTimeSeries"],
    queryFn: ({ signal }) => fetchTimeSeries(),
  });

  // Manually cache previous data
  const prevDataRef = useRef<TimeSeriesData | undefined>(queryResult.data);
  if (!queryResult.isFetching && queryResult.data) {
    prevDataRef.current = queryResult.data;
  }
  const data = queryResult.data ?? prevDataRef.current;

  if (queryResult.isLoading && !data) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (queryResult.isError) {
    return (
      <div className="text-red-600">
        Failed to load time series data.{" "}
        <button onClick={() => queryResult.refetch()}>Retry</button>
      </div>
    );
  }

  return <LineChart data={data?.points || []} />;
}