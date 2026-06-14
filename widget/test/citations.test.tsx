// widget/test/citations.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Citations } from "@/components/Citations";

const citations = [
  { id: 1, github_url: "https://github.com/me/r/blob/main/api.ts", repo: "r", path: "api.ts", snippet: "import axios" },
  { id: 2, github_url: "https://github.com/me/r/blob/main/auth.ts", repo: "r", path: "auth.ts", snippet: "jwt.verify" },
];

describe("Citations", () => {
  it("renders one clickable GitHub link per citation", () => {
    render(<Citations citations={citations} />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "https://github.com/me/r/blob/main/api.ts");
    expect(links[0]).toHaveAttribute("target", "_blank");
  });

  it("expands an evidence snippet on demand", () => {
    render(<Citations citations={citations} />);
    expect(screen.queryByText("import axios")).not.toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /evidence/i })[0]);
    expect(screen.getByText("import axios")).toBeInTheDocument();
  });

  it("renders nothing when there are no citations", () => {
    const { container } = render(<Citations citations={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
