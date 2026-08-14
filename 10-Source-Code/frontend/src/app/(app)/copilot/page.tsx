"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { aiApiClient, ApiError } from "@/lib/api-client";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { QueryResponse, SourceRef } from "@/lib/types";

interface ChatMessage {
  role: "user" | "assistant" | "error";
  text: string;
  sources?: SourceRef[];
}

const SUGGESTIONS = [
  "Which equipment has the highest risk?",
  "Summarize open findings across all assets",
  "What is the remaining life of V-101?",
];

export default function CopilotPage() {
  // Session-only history — no persistence, matches the "no chat storage" scope of this
  // pass (the AI service itself is stateless per-request; see AI-Copilot-Design.md §3).
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function ask(q: string) {
    if (!q.trim() || isLoading) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setQuestion("");
    setIsLoading(true);
    try {
      const result = await aiApiClient.post<QueryResponse>("/ai/query", { question: q });
      setMessages((m) => [...m, { role: "assistant", text: result.answer, sources: result.sources }]);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "AI Copilot request failed";
      setMessages((m) => [...m, { role: "error", text: message }]);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await ask(question);
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-3xl flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">AI Asset Integrity Copilot</h1>
        <p className="text-sm text-muted-foreground">
          Ask questions about assets, risk, inspections, and findings — answers are scoped to
          your organization and cite the underlying records (FR-31).
        </p>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardContent className="flex flex-1 flex-col gap-3 overflow-y-auto pt-4">
          {messages.length === 0 && (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
              <p className="text-sm text-muted-foreground">Try asking:</p>
              <div className="flex flex-col gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => ask(s)}
                    className="rounded-md border border-border px-3 py-2 text-sm text-muted-foreground hover:bg-muted"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}>
              <div
                className={cn(
                  "max-w-[80%] rounded-lg px-3 py-2 text-sm",
                  m.role === "user" && "bg-primary text-primary-foreground",
                  m.role === "assistant" && "bg-muted text-foreground",
                  m.role === "error" && "bg-destructive/10 text-destructive",
                )}
              >
                <p className="whitespace-pre-wrap">{m.text}</p>
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1 border-t border-border/50 pt-2">
                    {m.sources.map((s, si) => (
                      <span
                        key={si}
                        className="rounded border border-border bg-card px-1.5 py-0.5 text-[10px] text-muted-foreground"
                      >
                        {s.type}:{s.id.slice(0, 8)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">Thinking…</div>
            </div>
          )}
          <div ref={bottomRef} />
        </CardContent>

        <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border p-3">
          <Input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about assets, risk, or inspections…"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !question.trim()}>
            Send
          </Button>
        </form>
      </Card>
    </div>
  );
}
