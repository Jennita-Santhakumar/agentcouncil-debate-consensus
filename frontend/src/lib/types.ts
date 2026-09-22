export interface ScoreBreakdown {
  logical_strength: number;
  evidence_quality: number;
  clarity: number;
  counterargument_handling: number;
  feedback: string;
  total: number;
}

export interface RoundOut {
  round_number: number;
  pro_argument: string;
  pro_score_breakdown: ScoreBreakdown;
  con_argument: string;
  con_score_breakdown: ScoreBreakdown;
}

export interface DebateSummary {
  id: string;
  topic: string;
  num_rounds: number;
  status: "running" | "completed" | "failed";
  pro_score: number;
  con_score: number;
  winner: "pro" | "con" | "tie" | null;
  created_at: string;
}

export interface DebateDetail extends DebateSummary {
  completed_at: string | null;
  rounds: RoundOut[];
}

export type WsMessage =
  | {
      type: "round_complete";
      debate_id: string;
      round_number: number;
      pro_argument: string;
      pro_score_breakdown: ScoreBreakdown;
      con_argument: string;
      con_score_breakdown: ScoreBreakdown;
      running_pro_score: number;
      running_con_score: number;
    }
  | {
      type: "debate_complete";
      debate_id: string;
      winner: "pro" | "con" | "tie";
      pro_score: number;
      con_score: number;
    }
  | {
      type: "debate_failed";
      debate_id: string;
      error: string;
    };
