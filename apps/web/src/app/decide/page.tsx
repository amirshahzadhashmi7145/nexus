"use client";

import { FormEvent, useState } from "react";
import { SiteNav } from "@/components/SiteNav";
import {
  analyzePriceChange,
  fetchAudit,
  money,
  resolveDecision,
  type AuditEvent,
  type PriceDecision,
} from "@/lib/api";

const DEMO = {
  sku: "P-0001",
  pct: "-10",
  sims: "100",
} as const;

export default function DecidePage() {
  const [sku, setSku] = useState<string>(DEMO.sku);
  const [pct, setPct] = useState<string>(DEMO.pct);
  const [sims, setSims] = useState<string>(DEMO.sims);
  const [loading, setLoading] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PriceDecision | null>(null);
  const [humanStatus, setHumanStatus] = useState<string | null>(null);
  const [audit, setAudit] = useState<AuditEvent[]>([]);

  async function runAnalyze(nextSku: string, nextPct: string, nextSims: string) {
    setLoading(true);
    setError(null);
    setHumanStatus(null);
    setAudit([]);
    try {
      const data = await analyzePriceChange({
        sku: nextSku.trim(),
        price_change_pct: Number(nextPct),
        simulations: Number(nextSims),
        horizon_days: 30,
        seed: 42,
      });
      setResult(data);
      setHumanStatus("pending");
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await runAnalyze(sku, pct, sims);
  }

  async function onDemoClick() {
    setSku(DEMO.sku);
    setPct(DEMO.pct);
    setSims(DEMO.sims);
    await runAnalyze(DEMO.sku, DEMO.pct, DEMO.sims);
  }

  async function onResolve(action: "approve" | "reject") {
    if (!result) return;
    setResolving(true);
    setError(null);
    try {
      const record = await resolveDecision(result.decision_id, action, {
        actor: "human",
        note: action === "approve" ? "Approved in NEXUS UI" : "Rejected in NEXUS UI",
      });
      setHumanStatus(record.status);
      const events = await fetchAudit(8);
      setAudit(events);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Resolve failed");
    } finally {
      setResolving(false);
    }
  }

  return (
    <div className="shell">
      <SiteNav />

      <section className="hero">
        <p className="eyebrow">Decision desk</p>
        <h1>Decide</h1>
        <p>
          One run: policy research, twin state, Monte Carlo, critic, then your
          approval.
        </p>
        <div className="cta-row">
          <button
            className="btn btn-primary"
            type="button"
            disabled={loading}
            onClick={onDemoClick}
          >
            {loading ? "Running…" : "Run P-0001 −10%"}
          </button>
        </div>
      </section>

      <div className="stack">
        <section className="block">
          <h2>Scenario</h2>
          <p className="muted" style={{ marginBottom: "0.85rem" }}>
            Seeded catalog defaults. Seed stays 42 for repeatable demos.
          </p>
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
              {loading ? "Running…" : "Analyze"}
            </button>
          </form>
          {error ? <p className="error">{error}</p> : null}
        </section>

        {result ? (
          <section className="block result-enter">
            <div className="status-row">
              <span className={`status ${result.approve ? "status-ok" : "status-warn"}`}>
                System · {result.approve ? "approve signal" : "hold"}
              </span>
              {humanStatus ? (
                <span
                  className={`status ${humanStatus === "approved" ? "status-ok" : "status-warn"}`}
                >
                  Human · {humanStatus}
                </span>
              ) : null}
            </div>
            <h2>{result.decision_id}</h2>
            <p style={{ marginBottom: "0.35rem", lineHeight: 1.5 }}>{result.recommendation}</p>

            <div className="metrics">
              <div className="metric">
                <span>Expected revenue</span>
                <strong>{money(result.simulation.expected_revenue)}</strong>
              </div>
              <div className="metric">
                <span>Expected profit</span>
                <strong>{money(result.simulation.expected_profit)}</strong>
              </div>
              <div className="metric">
                <span>Stockout</span>
                <strong>{(result.simulation.stockout_probability * 100).toFixed(1)}%</strong>
              </div>
            </div>

            {humanStatus === "pending" ? (
              <div className="cta-row" style={{ marginBottom: "1.1rem" }}>
                <button
                  className="btn btn-primary"
                  type="button"
                  disabled={resolving}
                  onClick={() => onResolve("approve")}
                >
                  {resolving ? "Saving…" : "Approve"}
                </button>
                <button
                  className="btn btn-ghost"
                  type="button"
                  disabled={resolving}
                  onClick={() => onResolve("reject")}
                >
                  Reject
                </button>
              </div>
            ) : null}

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

            <h2 style={{ marginTop: "1.1rem" }}>Risks</h2>
            <ul className="list-plain">
              {result.risks.map((risk) => (
                <li key={risk}>{risk}</li>
              ))}
            </ul>

            {result.next_actions.length > 0 ? (
              <>
                <h2 style={{ marginTop: "1.1rem" }}>Next actions</h2>
                <ul className="list-plain">
                  {result.next_actions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
              </>
            ) : null}
          </section>
        ) : null}

        {audit.length > 0 ? (
          <section className="block result-enter">
            <h2>Audit</h2>
            <div className="trace">
              {audit.map((event) => (
                <div className="step" key={event.id}>
                  <strong>
                    {event.action} · {event.entity_type}/{event.entity_id}
                  </strong>
                  <span>
                    {event.actor}
                    {event.detail ? ` — ${event.detail}` : ""}
                  </span>
                </div>
              ))}
            </div>
          </section>
        ) : null}
      </div>
    </div>
  );
}
