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
        <h1>NEXUS</h1>
        <p>
          Simulate decisions. Discover better strategies. Act with confidence —
          NovaCart digital twin for the lablab.ai × AMD hackathon.
        </p>
        <div className="cta-row">
          <Link className="btn btn-primary" href="/decide">
            Analyze a price change
          </Link>
          <a className="btn btn-ghost" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            API docs
          </a>
        </div>
      </section>

      <section className="panel">
        <h2>NovaCart twin snapshot</h2>
        {error ? (
          <p className="error">{error}</p>
        ) : twin ? (
          <div className="metrics">
            <div className="metric">
              <span>Revenue</span>
              <strong>{money(twin.revenue)}</strong>
            </div>
            <div className="metric">
              <span>Profit</span>
              <strong>{money(twin.profit)}</strong>
            </div>
            <div className="metric">
              <span>Inventory units</span>
              <strong>{twin.inventory_units}</strong>
            </div>
            <div className="metric">
              <span>Orders</span>
              <strong>{twin.order_count}</strong>
            </div>
            <div className="metric">
              <span>Customers</span>
              <strong>{twin.customer_count}</strong>
            </div>
            <div className="metric">
              <span>Low-stock SKUs</span>
              <strong>{twin.low_stock_skus.length}</strong>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  );
}
