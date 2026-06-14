// widget/test/api.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { sendChat } from "@/lib/api";

beforeEach(() => {
  vi.stubEnv("VITE_CHAT_API_URL", "https://api.test/chat");
  vi.restoreAllMocks();
});

describe("sendChat", () => {
  it("POSTs the message and returns the parsed response", async () => {
    const payload = { answer: "Hi[1]", citations: [{ id: 1, github_url: "u", snippet: "s" }], sessionId: "s1" };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => payload });
    vi.stubGlobal("fetch", fetchMock);

    const result = await sendChat({ message: "hello", sessionId: "s1", repo: "r" });

    expect(fetchMock).toHaveBeenCalledWith("https://api.test/chat", expect.objectContaining({ method: "POST" }));
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body).toEqual({ message: "hello", sessionId: "s1", repo: "r" });
    expect(result.answer).toBe("Hi[1]");
  });

  it("throws on non-ok responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 502 }));
    await expect(sendChat({ message: "x" })).rejects.toThrow();
  });
});
