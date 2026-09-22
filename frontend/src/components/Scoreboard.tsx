interface Props {
  proScore: number;
  conScore: number;
  winner?: "pro" | "con" | "tie" | null;
}

export default function Scoreboard({ proScore, conScore, winner }: Props) {
  const total = proScore + conScore || 1;
  const proPct = (proScore / total) * 100;

  return (
    <div className="rounded-xl border border-white/10 bg-ink-800/60 p-4">
      <div className="mb-2 flex items-center justify-between font-mono text-sm">
        <span className={`font-bold ${winner === "pro" ? "text-pro-light" : "text-white/70"}`}>
          Pro {proScore.toFixed(1)}
          {winner === "pro" && " – Winner"}
        </span>
        <span className={`font-bold ${winner === "con" ? "text-con-light" : "text-white/70"}`}>
          Con {conScore.toFixed(1)}
          {winner === "con" && " – Winner"}
        </span>
      </div>
      <div className="flex h-2.5 overflow-hidden rounded-full bg-white/10">
        <div className="h-full bg-pro transition-all duration-500" style={{ width: `${proPct}%` }} />
        <div className="h-full bg-con transition-all duration-500" style={{ width: `${100 - proPct}%` }} />
      </div>
      {winner === "tie" && <p className="mt-2 text-center text-xs text-white/50">Debate ended in a tie.</p>}
    </div>
  );
}
