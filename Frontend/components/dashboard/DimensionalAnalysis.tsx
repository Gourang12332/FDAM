"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "../ui/skeleton";
import { BarChart } from "recharts"; // Assume a BarChart component exists

interface Dimension {
  name: string;
  predictedFraud: number;
  reportedFraud: number;
}

interface DimensionalData {
  dimensions: Dimension[];
}

const fetchDimensional = async (): Promise<DimensionalData> => {
  const response = await fetch("/api/dashboard/dimensional");
  if (!response.ok) throw new Error("Failed to fetch dimensional data");
  return response.json();
};

export default function DimensionalAnalysis() {
  const queryResult = useQuery<DimensionalData, Error>({
    queryKey: ["dashboardDimensional"],
    queryFn: ({ signal }) => fetchDimensional(),
  });

  // Manually cache previous data
  const prevDataRef = useRef<DimensionalData | undefined>(queryResult.data);
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
        Failed to load dimensional data.{" "}
        <button onClick={() => queryResult.refetch()}>Retry</button>
      </div>
    );
  }

  return <BarChart data={data?.dimensions || []} />;
}