"use client";

import { useState } from "react";
import { DatePicker } from "@/components/ui/date-picker";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export interface FiltersData {
  startDate: Date | undefined;
  endDate: Date | undefined;
  payerId: string;
  payeeId: string;
  searchQuery: string;
}

interface FiltersProps {
  filters: FiltersData;
  setFilters: (filters: FiltersData) => void;
}

export default function Filters({ filters, setFilters }: FiltersProps) {
  const [localFilters, setLocalFilters] = useState<FiltersData>(filters);

  const applyFilters = () => {
    setFilters(localFilters);
  };

  const clearFilters = () => {
    const cleared = {
      startDate: new Date(new Date().setMonth(new Date().getMonth() - 1)),
      endDate: new Date(),
      payerId: "all",    // changed from "" to "all"
      payeeId: "all",    // changed from "" to "all"
      searchQuery: "",
    };
    setLocalFilters(cleared);
    setFilters(cleared);
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-sabpaisa-primary p-4 mb-6">
      <h2 className="text-lg font-medium text-sabpaisa-primary mb-4">
        Filters
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Date range picker */}
        <div className="flex flex-col space-y-2">
          <label className="text-sm font-medium text-sabpaisa-text">
            Date Range
          </label>
          <div className="flex items-center space-x-2">
            <DatePicker
              date={localFilters.startDate}
              onSelect={(date) =>
                setLocalFilters({ ...localFilters, startDate: date })
              }
            />
            <span className="text-sabpaisa-muted">to</span>
            <DatePicker
              date={localFilters.endDate}
              onSelect={(date) =>
                setLocalFilters({ ...localFilters, endDate: date })
              }
            />
          </div>
        </div>
        {/* Transaction search */}
        <div className="flex flex-col space-y-2">
          <label className="text-sm font-medium text-sabpaisa-text">
            Transaction Search
          </label>
          <Input
            placeholder="Search by Transaction ID"
            value={localFilters.searchQuery}
            onChange={(e) =>
              setLocalFilters({ ...localFilters, searchQuery: e.target.value })
            }
          />
        </div>
        {/* Payer/Payee filters */}
        <div className="flex flex-col space-y-2">
          <label className="text-sm font-medium text-sabpaisa-text">
            Payer/Payee ID
          </label>
          <div className="flex space-x-2">
            <Select
              value={localFilters.payerId}
              onValueChange={(value) =>
                setLocalFilters({ ...localFilters, payerId: value })
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Payer ID" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Payers</SelectItem>
                <SelectItem value="P1234">P1234</SelectItem>
                <SelectItem value="P5678">P5678</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={localFilters.payeeId}
              onValueChange={(value) =>
                setLocalFilters({ ...localFilters, payeeId: value })
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Payee ID" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Payees</SelectItem>
                <SelectItem value="M1234">M1234</SelectItem>
                <SelectItem value="M5678">M5678</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
      <div className="flex justify-end space-x-3 mt-4">
        <Button
          variant="outline"
          className="border-sabpaisa-primary text-sabpaisa-primary"
          onClick={clearFilters}
        >
          Clear Filters
        </Button>
        <Button
          className="bg-sabpaisa-primary text-white"
          onClick={applyFilters}
        >
          Apply Filters
        </Button>
      </div>
    </div>
  );
}