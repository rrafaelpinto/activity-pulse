import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InfoPopover } from "./InfoPopover";

function setup() {
  render(
    <div>
      <InfoPopover label="About the usual week">Median of the last weeks.</InfoPopover>
      <InfoPopover label="About the change" align="end">Percentage against usual.</InfoPopover>
      <button type="button">Elsewhere</button>
    </div>,
  );
  return {
    usual: screen.getByRole("button", { name: "About the usual week" }),
    change: screen.getByRole("button", { name: "About the change" }),
  };
}

describe("InfoPopover", () => {
  it("is closed until the button is clicked, and tells assistive tech about its state", async () => {
    const { usual } = setup();
    expect(usual).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByText("Median of the last weeks.")).not.toBeInTheDocument();

    await userEvent.click(usual);

    expect(usual).toHaveAttribute("aria-expanded", "true");
    const text = screen.getByText("Median of the last weeks.");
    expect(text).toBeVisible();
    expect(usual).toHaveAttribute("aria-controls", text.id);
  });

  it("toggles closed on a second click", async () => {
    const { usual } = setup();
    await userEvent.click(usual);
    await userEvent.click(usual);
    expect(screen.queryByText("Median of the last weeks.")).not.toBeInTheDocument();
    expect(usual).toHaveAttribute("aria-expanded", "false");
    expect(usual).not.toHaveAttribute("aria-controls");
  });

  it("opens and closes from the keyboard with Enter and Space", async () => {
    const { usual } = setup();
    usual.focus();

    await userEvent.keyboard("{Enter}");
    expect(screen.getByText("Median of the last weeks.")).toBeInTheDocument();
    await userEvent.keyboard(" ");
    expect(screen.queryByText("Median of the last weeks.")).not.toBeInTheDocument();
  });

  it("closes with Escape and returns focus to the button", async () => {
    const { usual } = setup();
    await userEvent.click(usual);
    await userEvent.click(screen.getByText("Median of the last weeks.")); // focus moves into the popover

    await userEvent.keyboard("{Escape}");

    expect(screen.queryByText("Median of the last weeks.")).not.toBeInTheDocument();
    expect(usual).toHaveFocus();
  });

  it("stays open while its own text is clicked", async () => {
    const { usual } = setup();
    await userEvent.click(usual);
    await userEvent.click(screen.getByText("Median of the last weeks."));
    expect(screen.getByText("Median of the last weeks.")).toBeInTheDocument();
  });

  it("closes when something else is clicked", async () => {
    const { usual } = setup();
    await userEvent.click(usual);
    await userEvent.click(screen.getByRole("button", { name: "Elsewhere" }));
    expect(screen.queryByText("Median of the last weeks.")).not.toBeInTheDocument();
  });

  it("closes on a press outside even if focus never moved (Safari does not focus buttons on click)", async () => {
    const { usual } = setup();
    await userEvent.click(usual);

    fireEvent.pointerDown(document.body); // no focus change, so only the outside-press handler can close it

    expect(screen.queryByText("Median of the last weeks.")).not.toBeInTheDocument();
  });

  it("closes when keyboard focus leaves it", async () => {
    const { usual } = setup();
    usual.focus();
    await userEvent.keyboard("{Enter}");

    await userEvent.tab(); // next focusable: the other popover's button

    expect(screen.queryByText("Median of the last weeks.")).not.toBeInTheDocument();
  });

  it("shows one popover at a time", async () => {
    const { usual, change } = setup();
    await userEvent.click(usual);
    await userEvent.click(change);

    expect(screen.queryByText("Median of the last weeks.")).not.toBeInTheDocument();
    expect(screen.getByText("Percentage against usual.")).toBeInTheDocument();
  });
});
