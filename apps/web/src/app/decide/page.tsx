"use client";

import { FormEvent, useState } from "react";
import { SiteNav } from "@/components/SiteNav";
import { analyzePriceChange, money, type PriceDecision } from "@/lib/api";

export default function DecidePage() {
  const [sku, setSku] = useState("P-0001");
  const [pct, setPct] = useState("-10");
  const [sims, setSims] = useState("100");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PriceDecision | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await analyzePriceChange({
        sku: sku.trim(),
        price_change_pct: Number(pct),
        simulations: Number(sims),
        horizon_days: 30,
        seed: 42,
      });
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="shell">
      <SiteNav />
      <section className="hero">
        <h1>Decide</h1>
        <p>
          Run the manager orchestrator: research policies, read the twin, simulate
          the price move, critique risk, then recommend.
        </p>
      </section>

      <div className="stack">
        <section className="panel">
          <h2>Price-change scenario</h2>
          <form onSubmit={onSubmit}>
            <div className="form-grid">
              <label>
                SKU
                <input value={sku} onChange={(e) => setSku(e.target.value)} required />
              </label>
              <label>
                Price change %
                <input value={pct} onChange={(e) => setPct(e.target.value)} required />
              </label>
              <label>
                Simulations
                <input value={sims} onChange={(e) => setSims(e.target.value)} required />
              </label>
            </div>
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? "Running agents…" : "Analyze"}
            </button>
          </form>
          {error ? <p className="error">{error}</p> : null}
        </section>

        {result ? (
          <section className="panel">
            <span className={`badge ${result.approve ? "badge-ok" : "badge-no"}`}>
              {result.approve ? "Approve signal" : "Do not auto-approve"}
            </span>
            <h2>{result.decision_id}</h2>
            <p style={{ marginBottom: "0.75rem" }}>{result.recommendation}</p>
            <div className="metrics" style={{ marginBottom: "1rem" }}>
              <div className="metric">
                <span>Expected revenue</span>
                <strong>{money(result.simulation.expected_revenue)}</strong>
              </div>
              <div className="metric">
                <span>Expected profit</span>
                <strong>{money(result.simulation.expected_profit)}</strong>
              </div>
              <div className="metric">
                <span>Stockout probability</span>
                <strong>{(result.simulation.stockout_probability * 100).toFixed(1)}%</strong>
              </div>
            </div>
            <h2>Agent trace</h2>
            <div className="trace">
              {result.agent_trace.map((step) => (
                <div className="step" key={`${step.agent}-${step.role}`}>
                  <strong>
                    {step.agent} — {step.role}
                  </strong>
                  <span>{step.summary}</span>
                </div>
              ))}
            </div>
            <h2 style={{ marginTop: "1rem" }}>Risks</h2>
            <ul className="muted" style={{ paddingLeft: "1.1rem" }}>
              {result.risks.map((risk) => (
                <li key={risk}>{risk}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </div>
  );
}
