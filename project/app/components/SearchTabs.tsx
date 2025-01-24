'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface SearchResult {
  title: string;
  description: string;
}

const commonSearches: Record<string, SearchResult[]> = {
  "recent": [
    { title: "How to reset password?", description: "Step-by-step guide for password reset" },
    { title: "Account settings", description: "Managing your account preferences" },
    { title: "Billing information", description: "Access and update payment details" }
  ],
  "popular": [
    { title: "Getting started guide", description: "Quick start guide for new users" },
    { title: "Feature overview", description: "Explore all available features" },
    { title: "Troubleshooting", description: "Common issues and solutions" }
  ],
  "faq": [
    { title: "What payment methods are accepted?", description: "List of supported payment options" },
    { title: "How to contact support?", description: "Ways to reach our support team" },
    { title: "Cancellation policy", description: "Understanding our cancellation terms" }
  ],
  "tutorials": [
    { title: "Basic navigation", description: "Learn to navigate the platform" },
    { title: "Advanced features", description: "Deep dive into advanced capabilities" },
    { title: "Tips and tricks", description: "Expert tips for better usage" }
  ]
};

export function SearchTabs() {
  return (
    <div className="mt-8">
      <Card>
        <CardHeader>
          <CardTitle>Knowledge Base</CardTitle>
          <CardDescription>
            Find answers to common questions and explore our comprehensive guides to make the most of our platform.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="recent" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="recent">Recent</TabsTrigger>
              <TabsTrigger value="popular">Popular</TabsTrigger>
              <TabsTrigger value="faq">FAQ</TabsTrigger>
              <TabsTrigger value="tutorials">Tutorials</TabsTrigger>
            </TabsList>
            {Object.entries(commonSearches).map(([key, results]) => (
              <TabsContent key={key} value={key}>
                <ScrollArea className="h-[200px] w-full rounded-md border p-4">
                  <div className="space-y-4">
                    {results.map((result, index) => (
                      <div key={index} className="space-y-1">
                        <h3 className="text-sm font-medium leading-none">{result.title}</h3>
                        <p className="text-sm text-muted-foreground">{result.description}</p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}