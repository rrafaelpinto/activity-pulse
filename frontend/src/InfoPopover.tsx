import { useEffect, useId, useRef, useState, type ReactNode } from "react";

interface Props {
  /** Accessible name of the button, e.g. "About the usual week". */
  label: string;
  /** Which edge of the button the popover lines up with on wide screens. */
  align?: "start" | "end";
  children: ReactNode;
}

/**
 * A small "i" button that shows a short explanation on click or tap. Opens and closes with
 * Enter/Space, closes with Escape (focus returns to the button), when focus leaves, or when
 * something else is clicked.
 */
export function InfoPopover({ label, align = "start", children }: Props) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const root = useRef<HTMLSpanElement>(null);
  const button = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      button.current?.focus();
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <span
      className="info"
      ref={root}
      onBlur={(event) => {
        if (!root.current?.contains(event.relatedTarget as Node | null)) setOpen(false);
      }}
    >
      <button
        type="button"
        ref={button}
        className="info-button"
        aria-label={label}
        aria-expanded={open}
        aria-controls={open ? id : undefined}
        onClick={() => setOpen((value) => !value)}
      >
        <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
          <circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M8 7.2v4M8 4.6v.1" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      </button>
      {open && (
        <div id={id} className={`popover popover-${align}`} tabIndex={-1}>
          {children}
        </div>
      )}
    </span>
  );
}
