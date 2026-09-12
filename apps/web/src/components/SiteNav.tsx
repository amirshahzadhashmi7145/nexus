import Link from "next/link";

export function SiteNav() {
  return (
    <header className="topnav">
      <Link href="/" className="brand">
        NEXUS
      </Link>
      <nav className="nav-links">
        <Link href="/">Twin</Link>
        <Link href="/decide">Decide</Link>
      </nav>
    </header>
  );
}
