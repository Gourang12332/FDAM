
"use client"

import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

interface DatePickerProps {
  date?: Date
  onSelect: (date: Date | undefined) => void
}

export function DatePicker({ date, onSelect }: DatePickerProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant={"outline"}
          className={cn(
            "w-[240px] justify-start text-left font-normal bg-white border-sabpaisa-accent/30 hover:bg-sabpaisa-accent/5 hover:text-sabpaisa-primary hover:border-sabpaisa-accent transition-colors",
            !date && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4 text-sabpaisa-accent" />
          {date ? format(date, "PPP") : <span>Pick a date</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0 bg-white border-sabpaisa-accent/30 shadow-lg shadow-sabpaisa-primary/10">
        <Calendar
          mode="single"
          selected={date}
          onSelect={onSelect}
          initialFocus
          className="rounded-md border-sabpaisa-accent/30"
        />
      </PopoverContent>
    </Popover>
  )
}