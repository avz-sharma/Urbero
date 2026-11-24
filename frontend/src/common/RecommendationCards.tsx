import type { RecommendationCard } from "../api/types";
import { MathDrawer } from "./MathDrawer";
import { ConfidenceBadge } from "./ConfidenceBadge";

export function RecommendationCards({
  cards,
}: {
  cards: RecommendationCard[];
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {cards.map((card) => (
        <article
          key={card.id}
          className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-3"
        >
          <h3 className="font-bold">{card.title}</h3>
          <p className="text-sm">{card.why}</p>
          <p className="text-sm font-semibold">{card.quantified_impact}</p>
          <p className="text-xs">
            {card.station_metadata.source} ·{" "}
            {card.station_metadata.status === "modelled_live"
              ? "Modelled current estimate"
              : card.station_metadata.status}{" "}
            · {card.station_metadata.station} ·{" "}
            {card.station_metadata.distance_km.toFixed(2)} km
          </p>
          <p className="text-xs">
            Observed:{" "}
            {new Date(card.station_metadata.observed_at).toLocaleString()}
          </p>
          <ConfidenceBadge
            confidence={{
              level: card.data_confidence,
              reason: card.confidence_reason,
            }}
            showScore={false}
            showReason
          />
          <MathDrawer title={`Show the Math: ${card.title}`}>
            <p>{card.math_breakdown.formula_expression}</p>
            <dl>
              {Object.entries(card.math_breakdown.inputs).map(
                ([key, value]) => (
                  <div key={key}>
                    <dt>{key.replace(/_/g, " ")}</dt>
                    <dd>
                      {typeof value === "object"
                        ? JSON.stringify(value)
                        : String(value)}
                    </dd>
                  </div>
                ),
              )}
            </dl>
            <p>Result: {String(card.math_breakdown.output_value)}</p>
            <p>{card.math_breakdown.reference_benchmark}</p>
            <p>{card.math_breakdown.scientific_citation}</p>
          </MathDrawer>
        </article>
      ))}
    </div>
  );
}
