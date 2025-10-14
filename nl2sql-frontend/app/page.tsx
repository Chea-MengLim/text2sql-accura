import { NL2SQLQuery } from '@/components/nl2sql-query';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold tracking-tight mb-2">
            NL2SQL AI Assistant
          </h1>
          <p className="text-lg text-muted-foreground">
            Transform natural language questions into SQL queries and visualizations
          </p>
        </div>

        {/* Main Query Interface */}
        <NL2SQLQuery />

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-muted-foreground">
          <p>Powered by Snowflake Arctic Text2SQL and Ollama AI</p>
        </footer>
      </div>
    </main>
  );
}
