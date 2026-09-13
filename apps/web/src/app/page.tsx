import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";
import { fetchDigitalTwin, money } from "@/lib/api";

export default async function HomePage() {
  let twin = null;
  let error: string | null = null;
  try {
    twin = await fetchDigitalTwin();
  } catch (err) {
    error = err instanceof Error ? err.message : "Could not load digital twin";
  }

  return (
    <div className="shell">
      <SiteNav />

      <section className="hero">
        <p className="eyebrow">NovaCart · lablab.ai × AMD</p>
        <h1>NEXUS</h1>
        <p>
          Simulate a price move against live twin data, company policy, and risk —
          then approve it with a full audit trail.
        </p>
        <div className="cta-row">
          <Link className="btn btn-primary" href="/decide">
            Start decision demo
          </Link>
          <a
            className="btn btn-ghost"
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
          >
            API
          </a>
        </div>
      </section>

      <p className="section-label">Live twin</p>
      {error ? (
        <p className="error">{error}</p>
      ) : twin ? (
        <div className="ticker">
          <div className="ticker-item">
            <span>Revenue</span>
            <strong>{money(twin.revenue)}</strong>
          </div>
          <div className="ticker-item">
            <span>Profit</span>
            <strong>{money(twin.profit)}</strong>
          </div>
          <div className="ticker-item">
            <span>Orders</span>
            <strong>{twin.order_count}</strong>
          </div>
          <div className="ticker-item">
            <span>Inventory</span>
            <strong>{twin.inventory_units}</strong>
          </div>
          <div className="ticker-item">
            <span>Customers</span>
            <strong>{twin.customer_count}</strong>
          </div>
          <div className="ticker-item">
            <span>Low stock</span>
            <strong>{twin.low_stock_skus.length}</strong>
          </div>
        </div>
      ) : null}

      <p className="section-label">Demo path</p>
      <div className="pipeline">
        <div className="pipeline-step">
          <strong>1 · Twin</strong>
          <p>Business truth from Postgres (or SQLite).</p>
        </div>
        <div className="pipeline-step">
          <strong>2 · Decide</strong>
          <p>RAG + simulation + agents on a −10% cut.</p>
        </div>
        <div className="pipeline-step">
          <strong>3 · Approve</strong>
          <p>Human sign-off lands in the audit log.</p>
        </div>
      </div>
    </div>
  );
}
