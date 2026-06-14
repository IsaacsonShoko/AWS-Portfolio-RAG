import type { ChatRequest, ChatResponse } from "./types";

export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  const API_URL = import.meta.env.VITE_CHAT_API_URL as string;
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: req.message, sessionId: req.sessionId, repo: req.repo }),
  });
  if (!res.ok) {
    throw new Error(`Chat request failed (${res.status})`);
  }
  return (await res.json()) as ChatResponse;
}
