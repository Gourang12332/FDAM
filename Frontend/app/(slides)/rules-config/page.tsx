// app/rules/page.tsx
"use client"

import { useState } from "react"
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts"



interface Condition {
  field: string;
  operator: string;
  value: string;
}

interface FormData {
  name: string;
  description: string;
  priority: string;
  status: string;
  conditions: Condition[];
  matchLogic: string;
}


export default function page() {
  const queryClient = useQueryClient();
  const [selectedRule, setSelectedRule] = useState<string | null>(null);

  const [formData, setFormData] = useState<FormData>({
    name: "",
    description: "",
    priority: "",
    status: "inactive",
    conditions: [],
    matchLogic: "all"
  });
  
  const defaultConditions: Condition[] = [
    { field: "amount", operator: "greater_than", value: "10000" },
    { field: "time", operator: "outside", value: "9:00-17:00" }
  ];
  
  const updateCondition = (index: number, field: keyof Condition, value: string): void => {
    const newConditions = [...formData.conditions];
    newConditions[index] = { ...newConditions[index], [field]: value };
    setFormData({ ...formData, conditions: newConditions });
  };
  
  const removeCondition = (index: number): void => {
    const newConditions = formData.conditions.filter((_, i) => i !== index);
    setFormData({ ...formData, conditions: newConditions });
  };
  
  const addCondition = (): void => {
    setFormData({
      ...formData,
      conditions: [...formData.conditions, { field: "amount", operator: "greater_than", value: "" }]
    });
  };
  
  // Sample rules data
  const rules = [
    { id: "R001", name: "High Amount Transaction", description: "Flag transactions over $10,000", priority: "High", status: "Active", triggeredCount: 145, falsePositiveRate: 12.3 },
    { id: "R002", name: "Unusual Location", description: "Transactions from high-risk countries", priority: "Medium", status: "Active", triggeredCount: 320, falsePositiveRate: 18.7 },
    { id: "R003", name: "Rapid Succession", description: "Multiple transactions within short time", priority: "High", status: "Inactive", triggeredCount: 78, falsePositiveRate: 9.2 },
    { id: "R004", name: "New Merchant", description: "First-time transaction with merchant", priority: "Low", status: "Active", triggeredCount: 215, falsePositiveRate: 27.4 },
    { id: "R005", name: "After Hours", description: "Transactions outside business hours", priority: "Medium", status: "Active", triggeredCount: 189, falsePositiveRate: 14.8 },
  ];
  
  // Rule performance data
  const rulePerformanceData = [
    { name: "R001", triggered: 145, falsePositives: 18 },
    { name: "R002", triggered: 320, falsePositives: 60 },
    { name: "R004", triggered: 215, falsePositives: 59 },
    { name: "R005", triggered: 189, falsePositives: 28 },
  ];
  
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      <div className="container mx-auto py-6">
        {/* Header */}
        <div className="rounded-xl bg-gradient-to-r from-sabpaisa-primary to-sabpaisa-accent p-6 mb-6 shadow-lg shadow-blue-500/10">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-black">Fraud Detection Rules</h1>
            <div className="flex space-x-2">
              <Button variant="outline" className="bg-white/10 text-black border-white/20 hover:bg-white/20">
                Import Rules
              </Button>
              <Button className="bg-white text-sabpaisa-primary hover:bg-white/90">
                Create New Rule
              </Button>
            </div>
          </div>
        </div>
        
        <Tabs defaultValue="rules" className="mb-6">
          <div className="bg-white p-1 rounded-lg border border-indigo-100 inline-block mb-4 shadow-sm">
            <TabsList className="grid grid-cols-3 w-[400px] bg-indigo-50">
              <TabsTrigger value="rules" className="data-[state=active]:bg-white data-[state=active]:text-indigo-700 data-[state=active]:shadow-sm">
                Rules List
              </TabsTrigger>
              <TabsTrigger value="editor" className="data-[state=active]:bg-white data-[state=active]:text-indigo-700 data-[state=active]:shadow-sm">
                Rule Editor
              </TabsTrigger>
              <TabsTrigger value="analytics" className="data-[state=active]:bg-white data-[state=active]:text-indigo-700 data-[state=active]:shadow-sm">
                Analytics
              </TabsTrigger>
            </TabsList>
          </div>
          
          {/* Rules Table Tab */}
          <TabsContent value="rules">
            <Card className="border-none shadow-lg shadow-blue-200/30">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
                <CardTitle className="text-blue-700">Fraud Detection Rules</CardTitle>
                <CardDescription>
                  Manage and configure rules used for fraud detection
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <div className="p-4 bg-white flex justify-between">
                  <div className="flex space-x-2 w-1/2">
                    <Input 
                      placeholder="Search rules..."
                      className="border-indigo-200 focus:ring-indigo-300"
                    />
                    <Button className="bg-indigo-600 text-white hover:bg-indigo-700">Search</Button>
                  </div>
                  <div className="flex space-x-2">
                    <Select defaultValue="all">
                      <SelectTrigger className="w-[180px] bg-white border-indigo-200">
                        <SelectValue placeholder="Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Statuses</SelectItem>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="inactive">Inactive</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select defaultValue="all">
                      <SelectTrigger className="w-[180px] bg-white border-indigo-200">
                        <SelectValue placeholder="Priority" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Priorities</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="low">Low</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="rounded-md">
                  <Table>
                    <TableHeader className="bg-slate-50">
                      <TableRow>
                        <TableHead className="text-slate-700">Rule ID</TableHead>
                        <TableHead className="text-slate-700">Name</TableHead>
                        <TableHead className="text-slate-700">Description</TableHead>
                        <TableHead className="text-slate-700">Priority</TableHead>
                        <TableHead className="text-slate-700">Status</TableHead>
                        <TableHead className="text-slate-700">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rules.map((rule) => (
                        <TableRow key={rule.id} className="hover:bg-blue-50 transition-colors">
                          <TableCell className="font-medium text-blue-600">{rule.id}</TableCell>
                          <TableCell className="font-medium">{rule.name}</TableCell>
                          <TableCell>{rule.description}</TableCell>
                          <TableCell>
                            <Badge 
                              className={
                                rule.priority === "High" ? "bg-red-100 text-red-700 hover:bg-red-200 border-red-200" :
                                rule.priority === "Medium" ? "bg-amber-100 text-amber-700 hover:bg-amber-200 border-amber-200" :
                                "bg-blue-100 text-blue-700 hover:bg-blue-200 border-blue-200"
                              }
                            >
                              {rule.priority}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center space-x-2">
                              <Switch checked={rule.status === "Active"} />
                              <span className={rule.status === "Active" ? "text-green-600" : "text-slate-500"}>
                                {rule.status}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex space-x-2">
                              <Button size="sm" variant="outline" className="h-8 border-blue-200 text-blue-600 hover:bg-blue-50"
                                onClick={() => setSelectedRule(rule.id)}>
                                Edit
                              </Button>
                              <Button size="sm" variant="outline" className="h-8 border-red-200 text-red-600 hover:bg-red-50">
                                Delete
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
                <div className="flex justify-between items-center p-4 bg-slate-50 border-t border-slate-200">
                  <div className="text-sm text-slate-500">
                    Showing 5 of 12 rules
                  </div>
                  <div className="flex space-x-2">
                    <Button variant="outline" size="sm" className="border-indigo-200 text-indigo-600 hover:bg-indigo-50">Previous</Button>
                    <Button variant="outline" size="sm" className="border-indigo-200 text-indigo-600 hover:bg-indigo-50">Next</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          
          
          {/* Rule Editor Tab */}
          <TabsContent value="editor">
  <Card className="border-none shadow-lg shadow-blue-200/30">
    <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50 border-b border-purple-100">
      <CardTitle className="text-purple-700">
        {selectedRule ? `Edit Rule: ${selectedRule}` : "Create New Rule"}
      </CardTitle>
      <CardDescription>
        Define conditions and actions for fraud detection
      </CardDescription>
    </CardHeader>
    <CardContent className="p-6 bg-white">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Basic Rule Information */}
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-indigo-700">Rule Name</Label>
            <Input 
              id="name" 
              placeholder="Enter rule name"
              className="border-indigo-200 focus:ring-indigo-300" 
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="description" className="text-indigo-700">Description</Label>
            <Textarea 
              id="description" 
              placeholder="Describe what this rule detects"
              className="border-indigo-200 focus:ring-indigo-300 min-h-24"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="priority" className="text-indigo-700">Priority</Label>
              <Select 
                value={formData.priority} 
                onValueChange={(value) => setFormData({...formData, priority: value})}
              >
                <SelectTrigger id="priority" className="bg-white border-indigo-200">
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="status" className="text-indigo-700">Status</Label>
              <Select 
                value={formData.status} 
                onValueChange={(value) => setFormData({...formData, status: value})}
              >
                <SelectTrigger id="status" className="bg-white border-indigo-200">
                  <SelectValue placeholder="Select status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
        
        {/* Rule Conditions Builder */}
        <div className="space-y-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <h3 className="text-lg font-semibold text-indigo-700">Conditions</h3>
          
          <div className="space-y-3">
            {formData.conditions.map((condition, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 bg-white rounded border border-slate-200">
                <Select 
                  value={condition.field}
                  onValueChange={(value) => updateCondition(index, "field", value)}
                >
                  <SelectTrigger className="w-[140px] bg-white border-slate-200">
                    <SelectValue placeholder="Field" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="amount">Amount</SelectItem>
                    <SelectItem value="channel">Channel</SelectItem>
                    <SelectItem value="paymentMode">Payment Mode</SelectItem>
                    <SelectItem value="location">Location</SelectItem>
                    <SelectItem value="time">Time of Day</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select 
                  value={condition.operator}
                  onValueChange={(value) => updateCondition(index, "operator", value)}
                >
                  <SelectTrigger className="w-[140px] bg-white border-slate-200">
                    <SelectValue placeholder="Operator" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="greater_than">Greater than</SelectItem>
                    <SelectItem value="less_than">Less than</SelectItem>
                    <SelectItem value="equal_to">Equal to</SelectItem>
                    <SelectItem value="contains">Contains</SelectItem>
                    <SelectItem value="outside">Outside range</SelectItem>
                    <SelectItem value="within">Within range</SelectItem>
                  </SelectContent>
                </Select>
                
                <Input 
                  placeholder="Value" 
                  className="border-slate-200"
                  value={condition.value}
                  onChange={(e) => updateCondition(index, "value", e.target.value)}
                />
                
                <Button 
                  variant="outline" 
                  className="border-red-200 text-red-600 p-2 h-8 w-8 rounded-full" 
                  size="sm"
                  onClick={() => removeCondition(index)}
                >
                  ✕
                </Button>
              </div>
            ))}
          </div>
          
          <div className="flex justify-between items-center pt-2">
            <Button 
              variant="outline" 
              size="sm" 
              className="text-indigo-600 border-indigo-200"
              onClick={addCondition}
            >
              + Add Condition
            </Button>
            
            <Select 
              value={formData.matchLogic} 
              onValueChange={(value) => setFormData({...formData, matchLogic: value})}
            >
              <SelectTrigger className="w-[140px] bg-white border-slate-200">
                <SelectValue placeholder="Logic" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Match ALL</SelectItem>
                <SelectItem value="any">Match ANY</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
      
      <div className="border-t border-slate-200 mt-6 pt-6 flex justify-between">
        <div className="space-x-2">
          <Button 
            variant="outline" 
            className="border-slate-200"
            onClick={() => {
              if (selectedRule) {
                // Reset to original rule data by fetching again
                fetch(`/api/rules/${selectedRule}`)
                  .then(res => res.json())
                  .then(ruleData => {
                    setFormData({
                      name: ruleData.name || "",
                      description: ruleData.description || "",
                      priority: ruleData.priority?.toLowerCase() || "medium",
                      status: ruleData.status?.toLowerCase() || "inactive",
                      conditions: ruleData.conditions || defaultConditions,
                      matchLogic: ruleData.matchLogic || "all"
                    });
                  });
              } else {
                // Reset to empty form
                setFormData({
                  name: "",
                  description: "",
                  priority: "",
                  status: "inactive",
                  conditions: defaultConditions,
                  matchLogic: "all"
                });
              }
            }}
          >
            Reset
          </Button>
          <Button variant="outline" className="border-indigo-200 text-indigo-600">
            Test Rule
          </Button>
        </div>
        <div className="space-x-2">
          <Button 
            variant="outline" 
            className="border-slate-200"
            onClick={() => setSelectedRule(null)}
          >
            Cancel
          </Button>
          <Button 
            className="bg-indigo-600 hover:bg-indigo-700"
            onClick={() => {
              const ruleData = {
                name: formData.name,
                description: formData.description,
                priority: formData.priority.charAt(0).toUpperCase() + formData.priority.slice(1),
                status: formData.status.charAt(0).toUpperCase() + formData.status.slice(1),
                conditions: formData.conditions,
                matchLogic: formData.matchLogic
              };
              
              if (selectedRule) {
                // Update existing rule
                fetch(`/api/rules/${selectedRule}`, {
                  method: 'PUT',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify(ruleData),
                })
                .then(response => {
                  if (response.ok) {
                    queryClient.invalidateQueries({ queryKey: ['rules'] });
                    setSelectedRule(null);
                  }
                });
              } else {
                // Create new rule
                fetch('/api/rules', {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify(ruleData),
                })
                .then(response => {
                  if (response.ok) {
                    queryClient.invalidateQueries({ queryKey: ['rules'] });
                    setFormData({
                      name: "",
                      description: "",
                      priority: "",
                      status: "inactive",
                      conditions: defaultConditions,
                      matchLogic: "all"
                    });
                  }
                });
              }
            }}
          >
            {selectedRule ? "Update Rule" : "Create Rule"}
          </Button>
        </div>
      </div>
    </CardContent>
  </Card>
</TabsContent>
          
          {/* Rules Analytics Tab */}
          <TabsContent value="analytics">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="border-none shadow-lg shadow-blue-200/30">
                <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50 border-b border-blue-100">
                  <CardTitle className="text-blue-700">Rule Performance</CardTitle>
                  <CardDescription>
                    Analytics showing how each rule is performing
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-[400px] bg-white p-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={rulePerformanceData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis dataKey="name" stroke="#64748b" />
                      <YAxis stroke="#64748b" />
                      <Tooltip contentStyle={{borderRadius: '8px', borderColor: '#cbd5e1'}} />
                      <Legend wrapperStyle={{paddingTop: '10px'}} />
                      <Bar 
                        dataKey="triggered" 
                        name="Triggered Count" 
                        fill="#4f46e5" 
                        radius={[4, 4, 0, 0]} 
                        barSize={30}
                      />
                      <Bar 
                        dataKey="falsePositives" 
                        name="False Positives" 
                        fill="#ef4444" 
                        radius={[4, 4, 0, 0]} 
                        barSize={30}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              
              <Card className="border-none shadow-lg shadow-blue-200/30">
                <CardHeader className="bg-gradient-to-r from-green-50 to-cyan-50 border-b border-green-100">
                  <CardTitle className="text-green-700">Rule Effectiveness</CardTitle>
                  <CardDescription>
                    Key metrics for your fraud detection rules
                  </CardDescription>
                </CardHeader>
                <CardContent className="bg-white">
                  <div className="grid grid-cols-2 gap-4 mt-2">
                    {rules.filter(r => r.status === "Active").map((rule) => (
                      <Card key={rule.id} className="border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all">
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm font-medium text-indigo-700 flex items-center justify-between">
                            <span>{rule.name}</span>
                            <Badge className={
                              rule.falsePositiveRate < 10 ? "bg-green-100 text-green-700" :
                              rule.falsePositiveRate < 20 ? "bg-amber-100 text-amber-700" :
                              "bg-red-100 text-red-700"
                            }>
                              {rule.falsePositiveRate}% FPR
                            </Badge>
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <div className="grid grid-cols-2 gap-1">
                            <div className="text-sm text-slate-500">Triggered:</div>
                            <div className="text-sm font-medium text-right">{rule.triggeredCount}</div>
                            <div className="text-sm text-slate-500">False Positives:</div>
                            <div className="text-sm font-medium text-right">{Math.round(rule.triggeredCount * rule.falsePositiveRate / 100)}</div>
                          </div>
                          <div className="mt-3 h-2 bg-slate-100 rounded-full">
                            <div 
                              className={`h-full rounded-full ${
                                rule.falsePositiveRate < 10 ? "bg-green-500" :
                                rule.falsePositiveRate < 20 ? "bg-amber-500" :
                                "bg-red-500"
                              }`} 
                              style={{ width: `${100 - rule.falsePositiveRate}%` }}
                            ></div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}   