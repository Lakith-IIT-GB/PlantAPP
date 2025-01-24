'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Leaf, Sprout, HelpCircle, BookOpen } from 'lucide-react';

interface SearchResult {
  title: string;
  description: string;
}

const commonSearches: Record<string, SearchResult[]> = {
  "recent": [
    { title: "How often should I water my succulents?", description: "Watering guide for succulent care" },
    { title: "Best indoor plants for low light", description: "Plants that thrive in shade" },
    { title: "Signs of overwatering", description: "Identifying and fixing water issues" }
  ],
  "popular": [
    { title: "Plant care basics", description: "Essential tips for beginners" },
    { title: "Seasonal plant care", description: "Adjusting care through seasons" },
    { title: "Common plant diseases", description: "Identifying and treating issues" }
  ],
  "faq": [
    { title: "Why are my plant's leaves turning yellow?", description: "Common causes and solutions" },
    { title: "Best fertilizers for indoor plants", description: "Nutrition guide for houseplants" },
    { title: "How to propagate plants", description: "Step-by-step propagation guide" }
  ],
  "tutorials": [
    { title: "Repotting guide", description: "When and how to repot plants" },
    { title: "Pruning techniques", description: "Maintaining plant shape and health" },
    { title: "Plant lighting guide", description: "Understanding light requirements" }
  ]
};

export function SearchTabs() {
  return (
    <div>
      <Card className="bg-background/50 backdrop-blur-sm border-primary/20">
        <CardHeader>
          <CardTitle className="text-primary flex items-center gap-2">
            <Sprout className="h-5 w-5" />
            Plant Care Knowledge Base
          </CardTitle>
          <CardDescription>
            Find expert advice and guides for keeping your plants healthy and thriving.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="recent" className="w-full">
            <TabsList className="grid w-full grid-cols-4 bg-secondary/50">
              <TabsTrigger value="recent" className="data-[state=active]:bg-primary/20">Recent</TabsTrigger>
              <TabsTrigger value="popular" className="data-[state=active]:bg-primary/20">Popular</TabsTrigger>
              <TabsTrigger value="faq" className="data-[state=active]:bg-primary/20">FAQ</TabsTrigger>
              <TabsTrigger value="tutorials" className="data-[state=active]:bg-primary/20">Tutorials</TabsTrigger>
            </TabsList>
            {Object.entries(commonSearches).map(([key, results]) => (
              <TabsContent key={key} value={key}>
                <ScrollArea className="h-[200px] w-full rounded-md border border-primary/20 bg-background/50 backdrop-blur-sm p-4">
                  <div className="space-y-4">
                    {results.map((result, index) => (
                      <div key={index} className="space-y-1">
                        <h3 className="text-sm font-medium leading-none text-primary flex items-center gap-2">
                          <Leaf className="h-4 w-4" />
                          {result.title}
                        </h3>
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