// widget/test/fourd-assistant.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { FourDAssistant } from "@/components/FourDAssistant";
import * as api from "@/lib/api";

beforeEach(() => vi.restoreAllMocks());

describe("FourDAssistant", () => {
  it("opens the panel from the launcher and shows starter questions", () => {
    render(<FourDAssistant />);
    fireEvent.click(screen.getByRole("button", { name: /open the 4d portfolio assistant/i }));
    expect(screen.getByText(/which projects use aws/i)).toBeInTheDocument();
  });

  it("sends a question and renders the answer with citations", async () => {
    vi.spyOn(api, "sendChat").mockResolvedValue({
      answer: "He used Axios.[1]",
      citations: [{ id: 1, github_url: "https://github.com/me/r/blob/main/api.ts", path: "api.ts", snippet: "import axios" }],
      sessionId: "s1",
    });
    render(<FourDAssistant />);
    fireEvent.click(screen.getByRole("button", { name: /open the 4d portfolio assistant/i }));
    fireEvent.click(screen.getByText(/what frameworks did he use for api calls/i));

    await waitFor(() => expect(screen.getByText("He used Axios.[1]")).toBeInTheDocument());
    expect(screen.getByRole("link", { name: /api\.ts/ })).toHaveAttribute(
      "href", "https://github.com/me/r/blob/main/api.ts",
    );
  });

  it("passes the returned sessionId on the next request", async () => {
    const spy = vi.spyOn(api, "sendChat")
      .mockResolvedValueOnce({ answer: "a", citations: [], sessionId: "sess-X" })
      .mockResolvedValueOnce({ answer: "b", citations: [], sessionId: "sess-X" });
    render(<FourDAssistant />);
    fireEvent.click(screen.getByRole("button", { name: /open the 4d portfolio assistant/i }));
    fireEvent.click(screen.getByText(/which projects use aws/i));
    await waitFor(() => expect(screen.getByText("a")).toBeInTheDocument());

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "follow up" } });
    fireEvent.submit(input.closest("form")!);
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(2));
    expect(spy.mock.calls[1][0].sessionId).toBe("sess-X");
  });
});
