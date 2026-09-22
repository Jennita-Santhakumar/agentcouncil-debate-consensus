import { useEffect, useRef, useState } from "react";
import { createDebate, debateWebSocketUrl, listDebates } from "../lib/api";
import type { DebateSummary, RoundOut, WsMessage } from "../lib/types";
import RoundCard from "./RoundCard";
import Scoreboard from "./Scoreboard";

type Phase = "idle" | "connecting" | "running" | "completed" | "failed";

export default function DebateArena() {
  const [topic, setTopic] = useState("");
  const [numRounds, setNumRounds] = useState(3);
  const [phase, setPhase] = useState<Phase>("idle");
  const [debateId, setDebateId] = useState<string | null>(null);
  const [rounds, setRounds] = useState<RoundOut[]>([]);
  const [proScore, setProScore] = useState(0);
  const [conScore, setConScore] = useState(0);
  const [winner, setWinner] = useState<"pro" | "con" | "tie" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<DebateSummary[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const refreshHistory = () => {
    listDebates()
      .then(setHistory)
      .catch(() => undefined);
  };

  useEffect(() => {
    refreshHistory();
    return () => wsRef.current?.close();
  }, []);

  const startDebate = async () => {
    if (topic.trim().length < 4) {
      setError("Topic must be at least 4 characters.");
      return;
    }
    setError(null);
    setRounds([]);
    setProScore(0);
    setConScore(0);
    setWinner(null);
    setPhase("connecting");

    try {
      const { debate_id } = await createDebate(topic.trim(), numRounds);
      setDebateId(debate_id);

      const ws = new WebSocket(debateWebSocketUrl(debate_id));
      wsRef.current = ws;

      ws.onopen = () => setPhase("running");
      ws.onerror = () => setError("WebSocket connection error.");
      ws.onclose = () => refreshHistory();

      ws.onmessage = (event) => {
        const msg: WsMessage = JSON.parse(event.data);
        if (msg.type === "round_complete") {
          setRounds((prev) => [
            ...prev,
            {
              round_number: msg.round_number,
              pro_argument: msg.pro_argument,
              pro_score_breakdown: msg.pro_score_breakdown,
              con_argument: msg.con_argument,
              con_score_breakdown: msg.con_score_breakdown,
            },
          ]);
          setProScore(msg.running_pro_score);
          setConScore(msg.running_con_score);
        } else if (msg.type === "debate_complete") {
          setProScore(msg.pro_score);
          setConScore(msg.con_score);
          setWinner(msg.winner);
          setPhase("completed");
          ws.close();
        } else if (msg.type === "debate_failed") {
          setError(msg.error);
          setPhase("failed");
          ws.close();
        }
      };
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start debate.");
      setPhase("idle");
    }
  };

  const isBusy = phase === "connecting" || phase === "running";

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
          Debate <span className="text-pro-light">Arena</span>
        </h1>
        <p className="mt-2 text-sm text-white/50">
          Two LangChain agents argue Pro and Con. An impartial Evaluator agent scores every round live.
        </p>
      </header>

      <div className="mb-8 rounded-xl border border-white/10 bg-ink-800/60 p-4">
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className="flex-1 rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white placeholder-white/30 outline-none focus:border-pro"
            placeholder="e.g. Should AI development be paused for safety research?"
            value={topic}
            disabled={isBusy}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !isBusy && startDebate()}
          />
          <select
            className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white outline-none"
            value={numRounds}
            disabled={isBusy}
            onChange={(e) => setNumRounds(Number(e.target.value))}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n} round{n > 1 ? "s" : ""}
              </option>
            ))}
          </select>
          <button
            onClick={startDebate}
            disabled={isBusy}
            className="rounded-lg bg-pro px-5 py-2 text-sm font-semibold text-white transition hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isBusy ? "Debating…" : "Start Debate"}
          </button>
        </div>
        {error && <p className="mt-2 text-xs text-con-light">{error}</p>}
        {isBusy && (
          <p className="mt-2 flex items-center gap-2 text-xs text-white/40">
            <span className="animate-pulse-dot h-1.5 w-1.5 rounded-full bg-pro-light" />
            {phase === "connecting" ? "Connecting…" : `Debate ${debateId?.slice(0, 8)} in progress`}
          </p>
        )}
      </div>

      {(rounds.length > 0 || phase === "running") && (
        <div className="mb-6">
          <Scoreboard proScore={proScore} conScore={conScore} winner={winner} />
        </div>
      )}

      {winner && (
        <div
          className={`mb-6 animate-fade-in-up rounded-xl border p-4 text-center text-sm font-semibold ${
            winner === "pro"
              ? "border-pro/40 bg-pro-bg/10 text-pro-light"
              : winner === "con"
                ? "border-con/40 bg-con-bg/10 text-con-light"
                : "border-white/20 bg-white/5 text-white/70"
          }`}
        >
          {winner === "tie" ? "This debate ended in a tie." : `${winner === "pro" ? "Pro" : "Con"} wins the debate.`}
        </div>
      )}

      <div className="space-y-4">
        {rounds.map((round) => (
          <RoundCard key={round.round_number} round={round} />
        ))}
      </div>

      <section className="mt-12">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-white/40">Debate History</h2>
        <div className="space-y-2">
          {history.length === 0 && <p className="text-sm text-white/30">No debates yet.</p>}
          {history.map((d) => (
            <div
              key={d.id}
              className="flex items-center justify-between rounded-lg border border-white/10 bg-ink-800/40 px-4 py-3 text-sm"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-white/80">{d.topic}</p>
                <p className="text-xs text-white/40">
                  {d.status} &middot; {d.num_rounds} rounds
                  {d.winner && ` · winner: ${d.winner}`}
                </p>
              </div>
              <div className="font-mono text-xs text-white/50">
                {d.pro_score.toFixed(1)} &ndash; {d.con_score.toFixed(1)}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
