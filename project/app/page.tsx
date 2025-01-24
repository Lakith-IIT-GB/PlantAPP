import { ChatInterface } from './components/ChatInterface';
import { SearchTabs } from './components/SearchTabs';

export default function Home() {
  return (
    <main className="container mx-auto p-4">
      <h1 className="text-2xl font-bold text-center mb-4">Chat Interface</h1>
      <SearchTabs />
      <div className="mt-8">
        <ChatInterface />
      </div>
    </main>
  );
}