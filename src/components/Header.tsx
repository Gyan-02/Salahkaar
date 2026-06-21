import { Menu, Sprout, X } from "lucide-react";
import { useState } from "react";
import { NavLink } from "react-router-dom";

export function Header() {
  const [open, setOpen] = useState(false);
  const links = [
    ["/", "Home"],
    ["/check", "Check readiness"],
    ["/demos", "Demo cases"],
    ["/guidelines", "Official guidelines"],
  ];
  return (
    <header className="site-header">
      <div className="nav-shell">
        <NavLink className="brand" to="/" onClick={() => setOpen(false)}>
          <span>
            <Sprout />
          </span>
          <div>
            <strong>Salahkaar</strong>
            <small>Benefits readiness · Bihar</small>
          </div>
        </NavLink>
        <button
          type="button"
          className="menu-button"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open ? <X /> : <Menu />}
        </button>
        <nav className={open ? "nav-open" : ""} aria-label="Primary navigation">
          {links.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
