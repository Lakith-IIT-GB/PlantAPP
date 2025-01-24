import { ChatInterface } from './components/ChatInterface';
import { SearchTabs } from './components/SearchTabs';

export default function Home() {
  return (
    <main className="container mx-auto p-4">
      <h1 className="text-4xl font-bold text-center mb-6 text-primary">Plant Care Assistant</h1>
      <div className="bg-background/80 backdrop-blur-sm p-6 rounded-xl shadow-xl">
        <SearchTabs />
        <div className="mt-4">
          <ChatInterface />
        </div>
      </div>
    </main>
  );
}