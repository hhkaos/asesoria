import { render, screen } from "@testing-library/react";
import App from "../App";

test("renders App without crashing", () => {
  render(<App />);
  expect(screen.getByText(/en construcción/i)).toBeInTheDocument();
});
