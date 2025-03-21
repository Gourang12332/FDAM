"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Filters, { FiltersData } from "@/components/dashboard/Filters";
import SummaryCards from "@/components/dashboard/TransactionTable";
import TransactionTable from "@/components/dashboard/DimensionalAnalysis";
import DimensionalAnalysis from "@/components/dashboard/DimensionalAnalysis";
import TimeSeriesAnalysis from "@/components/dashboard/TimeSeriesAnalysis";
import EvaluationMetrics from "@/components/dashboard/EvaluationMetrics";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";

export default function Page() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("transactions");
  const [filters, setFilters] = useState<FiltersData>({
    startDate: new Date(new Date().setMonth(new Date().getMonth() - 1)),
    endDate: new Date(),
    payerId: "",
    payeeId: "",
    searchQuery: "",
  });

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-sabpaisa-primary">
          Fraud Detection Dashboard
        </h1>
        <Button
          onClick={() => router.push("/rules-config")}
          className="bg-sabpaisa-secondary text-black hover:bg-sabpaisa-secondary/90 font-semibold shadow-md"
        >
          Rules Configuration
        </Button>
      </div>

      {/* Filters Section */}
      <Filters filters={filters} setFilters={setFilters} />

      {/* Summary Cards */}
      <SummaryCards filters={filters} />

      {/* Dashboard Tabs */}
      <Tabs defaultValue="transactions" className="mt-6">
        <TabsList>
          <TabsTrigger value="transactions" onClick={() => setActiveTab("transactions")}>
            Transactions
          </TabsTrigger>
          <TabsTrigger value="dimensional" onClick={() => setActiveTab("dimensional")}>
            Dimensional Analysis
          </TabsTrigger>
          <TabsTrigger value="timeseries" onClick={() => setActiveTab("timeseries")}>
            Time Series
          </TabsTrigger>
          <TabsTrigger value="evaluation" onClick={() => setActiveTab("evaluation")}>
            Evaluation Metrics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="transactions">
          <TransactionTable filters={filters} />
        </TabsContent>

        <TabsContent value="dimensional">
          <DimensionalAnalysis filters={filters} />
        </TabsContent>

        <TabsContent value="timeseries">
          <TimeSeriesAnalysis filters={filters} />
        </TabsContent>

        <TabsContent value="evaluation">
          <EvaluationMetrics filters={filters} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
