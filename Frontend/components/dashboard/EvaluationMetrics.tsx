"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "../ui/skeleton";

interface EvaluationData {
  confusionMatrix: number[][];
  precision: number;
  recall: number;
  f1Score: number;
}

const fetchEvaluation = async (): Promise<EvaluationData> => {
  const response = await fetch("/api/dashboard/evaluation");
  if (!response.ok) throw new Error("Failed to fetch evaluation data");
  return response.json();
};

export default function EvaluationMetrics() {
  const queryResult = useQuery<EvaluationData, Error>({
    queryKey: ["dashboardEvaluation"],
    queryFn: ({ signal }) => fetchEvaluation(),
  });

  // Manually cache previous data
  const prevDataRef = useRef<EvaluationData | undefined>(queryResult.data);
  if (!queryResult.isFetching && queryResult.data) {
    prevDataRef.current = queryResult.data;
  }
  const data = queryResult.data ?? prevDataRef.current;

  if (queryResult.isLoading && !data) {
    return <Skeleton className="h-32 w-full" />;
  }

  if (queryResult.isError) {
    return (
      <div className="text-red-600">
        Failed to load evaluation metrics.{" "}
        <button onClick={() => queryResult.refetch()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h4>Confusion Matrix</h4>
        <table>
          <tbody>
            {data?.confusionMatrix.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, colIndex) => (
                  <td key={colIndex} className="border px-2 py-1">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div>
        <p>Precision: {data?.precision}%</p>
        <p>Recall: {data?.recall}%</p>
        <p>F1 Score: {data?.f1Score}%</p>
      </div>
    </div>
  );
}