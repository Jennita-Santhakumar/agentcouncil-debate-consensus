import type { ScoreBreakdown } from "../lib/types";

interface Props {
  label: string;
  score: ScoreBreakdown;
  accent: "pro" | "con";
}

const SUB_SCORES: { key: keyof ScoreBreakdown; label: string; max: number }[] = [
  { key: "logical_strength", label: "Logic", max: 3 },
  { key: "evidence_quality", label: "Evidence", max: 3 },
  { key: "clarity", label: "Clarity", max: 2 },
  { key: "counterargument_handling", label: "Rebuttal", max: 2 },
];

export default function ScoreBadge({ label, score, accent }: Props) {
  const color = accent === "pro" ? "text-pro-light" : "text-con-light";
  const bar = accent === "pro" ? "bg-pro" : "bg-con";

  return (
    <div className="rounded-lg border border-white/10 bg-black/20 p-3">
      <div className="mb-2 flex items-baseline justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-white/50">{label}</span>
        <span className={`font-mono text-lg font-bold ${color}`}>{score.total.toFixed(1)}/10</span>
      </div>
      <div className="space-y-1.5">
        {SUB_SCORES.map((s) => (
          <div key={s.key} className="flex items-center gap-2 text-[11px]">
            <span className="w-16 shrink-0 text-white/40">{s.label}</span>
            <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
              <div
                className={`h-full rounded-full ${bar}`}
                style={{ width: `${(Number(score[s.key]) / s.max) * 100}%` }}
              />
            </div>
            <span className="w-8 text-right font-mono text-white/50">
              {Number(score[s.key]).toFixed(1)}/{s.max}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
