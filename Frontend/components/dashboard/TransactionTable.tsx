"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "../ui/skeleton";
import { Card } from "@/components/ui/card";

interface SummaryData {
  totalTransactions: number;
  fraudRate: number;
  averageTransactionAmount: number;
  falsePositiveRate: number;
}

const fetchSummary = async (): Promise<SummaryData> => {
  const response = await fetch("/api/dashboard/summary");
  if (!response.ok) throw new Error("Failed to fetch summary data");
  return response.json();
};

export default function SummaryCards() {
  const queryResult = useQuery<SummaryData, Error>({
    queryKey: ["dashboardSummary"],
    queryFn: ({ signal }) => fetchSummary(),
  });

  // Manually cache previous data
  const prevDataRef = useRef<SummaryData | undefined>(queryResult.data);
  if (!queryResult.isFetching && queryResult.data) {
    prevDataRef.current = queryResult.data;
  }
  const data = queryResult.data ?? prevDataRef.current;

  if (queryResult.isLoading && !data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-full" />
      </div>
    );
  }

  if (queryResult.isError) {
    return (
      <div className="text-red-600">
        Failed to load summary data.{" "}
        <button onClick={() => queryResult.refetch()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <h3>Total Transactions</h3>
        <p>{data?.totalTransactions}</p>
      </Card>
      <Card>
        <h3>Fraud Rate</h3>
        <p>{data?.fraudRate}%</p>
      </Card>
      <Card>
        <h3>Avg. Transaction</h3>
        <p>${data?.averageTransactionAmount.toFixed(2)}</p>
      </Card>
      <Card>
        <h3>False Positive Rate</h3>
        <p>{data?.falsePositiveRate}%</p>
      </Card>
    </div>
  );
}