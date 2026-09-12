const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type DigitalTwin = {
  organization: string;
  revenue: string;
  profit: string;
  inventory_units: number;
  order_count: number;
  customer_count: number;
  product_count: number;
  low_stock_skus: string[];
};

export type AgentStep = {
  agent: string;
  role: string;
  status: string;
  summary: string;
};

export type PriceDecision = {
  decision_id: string;
  question: string;
  plan: string[];
  agent_trace: AgentStep[];
  recommendation: string;
  approve: boolean;
  risks: string[];
  next_actions: string[];
  simulation: {
    expected_revenue: number;
    expected_profit: number;
    stockout_probability: number;
    risk_note: string;
  };
};

export type DecisionRecord = {
  decision_id: string;
  status: string;
  recommendation: string;
  decided_by: string | null;
  decision_note: string | null;
};

export async function fetchDigitalTwin(): Promise<DigitalTwin> {
  const res = await fetch(`${API_BASE}/api/v1/digital-twin`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Digital twin failed (${res.status}). Is the API running on ${API_BASE}?`);
  }
  return res.json();
}

export async function analyzePriceChange(body: {
  sku: string;
  price_change_pct: number;
  simulations: number;
  horizon_days: number;
  seed: number;
}): Promise<PriceDecision> {
  const res = await fetch(`${API_BASE}/api/v1/decisions/analyze-price-change`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Decision failed (${res.status})`);
  }
  return res.json();
}

export async function resolveDecision(
  decisionId: string,
  action: "approve" | "reject",
  body: { actor: string; note?: string },
): Promise<DecisionRecord> {
  const res = await fetch(`${API_BASE}/api/v1/decisions/${decisionId}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Resolve failed (${res.status})`);
  }
  return res.json();
}

export function money(value: string | number): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (Number.isNaN(n)) return String(value);
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}
