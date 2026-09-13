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
        <p className="eyebrow">lablab.ai × AMD · NovaCart MVP</p>
        <h1>NEXUS</h1>
        <p>
          Digital twin + policy RAG + Monte Carlo + multi-agent decisions — with a
          human in the loop. Built CPU-first; swap in vLLM on AMD when you are ready.
        </p>
        <div className="cta-row">
          <Link className="btn btn-primary" href="/decide">
            Run the 60-second demo
          </Link>
          <a className="btn btn-ghost" href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">
            API docs
          </a>
        </div>
      </section>

      <section className="panel demo-strip">
        <h2>What judges should see</h2>
        <ol className="flow-list">
          <li>
            <strong>Twin</strong> — live NovaCart metrics from the business DB
          </li>
          <li>
            <strong>Decide</strong> — one-click price cut; agents + simulation + policies
          </li>
          <li>
            <strong>Approve</strong> — human sign-off written to the audit log
          </li>
        </ol>
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
