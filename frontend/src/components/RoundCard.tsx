import type { RoundOut } from "../lib/types";
import ScoreBadge from "./ScoreBadge";

export default function RoundCard({ round }: { round: RoundOut }) {
  return (
    <div className="animate-fade-in-up rounded-xl border border-white/10 bg-ink-800/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-xs font-semibold text-white/70">
          Round {round.round_number}
        </span>
        <div className="h-px flex-1 bg-white/10" />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-pro" />
            <span className="text-sm font-semibold text-pro-light">Pro</span>
          </div>
          <p className="text-sm leading-relaxed text-white/80">{round.pro_argument}</p>
          <ScoreBadge label="Pro score" score={round.pro_score_breakdown} accent="pro" />
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-con" />
            <span className="text-sm font-semibold text-con-light">Con</span>
          </div>
          <p className="text-sm leading-relaxed text-white/80">{round.con_argument}</p>
          <ScoreBadge label="Con score" score={round.con_score_breakdown} accent="con" />
        </div>
      </div>
    </div>
  );
}
