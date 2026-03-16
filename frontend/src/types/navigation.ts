export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface CandidateElement {
  label: string;
  bbox: BoundingBox;
  confidence: number;
  is_chosen: boolean;
}

export interface DetectedElement {
  label: string;
  element_type: string;
  bbox: BoundingBox;
  confidence: number;
  interactable: boolean;
  accessibility_issues: string[];
}

export interface PerceptionResult {
  page_description: string;
  page_purpose: string;
  has_modal_or_overlay: boolean;
  loading_state: boolean;
  elements: DetectedElement[];
}

export type ActionType = "click" | "type" | "scroll_down" | "scroll_up" | "press_key" | "hover" | "wait" | "go_back" | "done";

export type FrictionSeverity = "low" | "medium" | "high" | "critical";

export interface ActionPlan {
  action_type: ActionType;
  target_element: string | null;
  coordinates: [number, number] | null;
  input_text: string | null;
  key: string | null;
  seconds: number | null;
  reasoning: string;
  confidence: number;
  candidates: CandidateElement[];
}

export type FrictionCategory = "navigation" | "contrast" | "affordance" | "copy" | "error" | "performance" | "accessibility";

export interface CategorizedFriction {
  category: FrictionCategory;
  description: string;
  severity: "low" | "medium" | "high" | "critical";
  evidence: string;
}

export interface EvaluationResult {
  progress_made: boolean;
  goal_achieved: boolean;
  page_changed: boolean;
  description: string;
  friction_detected: string[];
  friction_items?: CategorizedFriction[];
  confidence: number;
}

export interface ActionResult {
  success: boolean;
  url_after: string;
  error: string | null;
}

// Matches backend NavigationStep schema exactly
export interface NavigationStep {
  step_number: number;
  perception: PerceptionResult;
  plan: ActionPlan;
  action_result: ActionResult;
  evaluation: EvaluationResult;
  screenshot_before_b64: string;
  screenshot_after_b64: string;
  screenshot_before_url?: string;
  screenshot_after_url?: string;
  timestamp: string;
  is_recovery: boolean;
  recovery_reason: string | null;
}

// Real-time thought events from the PPAE loop
export interface ThoughtEvent {
  type: "thought";
  phase: "perceive" | "plan" | "act" | "evaluate";
  message: string;
  data?: Record<string, unknown>;
}

export interface NavigationMetrics {
  total_steps: number;
  retries: number;
  backtracks: number;
  time_seconds: number;
  friction_count: number;
  outcome: string;
  recovery_steps: number;
}

export interface SessionData {
  id: string;
  url: string;
  goal: string;
  persona: string | null;
  status: string;
  total_steps: number;
  completed: boolean;
}

// Matches backend PersonaConfig schema
export interface PersonaConfig {
  key: string;
  name: string;
  description: string;
  prompt_suffix: string;
  evaluation_suffix: string;
  behavior_modifiers: Record<string, unknown>;
}

export interface PathStep {
  step: number;
  action: string;
  target: string | null;
  friction: boolean;
  url: string;
}

export interface PersonaRunResult {
  persona_key: string;
  persona_name: string;
  total_steps: number;
  retries: number;
  backtracks: number;
  time_seconds: number;
  friction_count: number;
  friction_by_category: Record<string, number>;
  friction_score: number;
  ux_risk_index: number;
  outcome: string;
  session_id: string;
  path: PathStep[];
  verdict: string;
}

export interface ComparisonResult {
  url: string;
  goal: string;
  results: PersonaRunResult[];
}

// Matches backend FrictionItem schema
export interface FrictionItem {
  category: FrictionCategory;
  description: string;
  severity: FrictionSeverity;
  evidence_step: number;
  evidence_screenshot_url: string;
  improvement_suggestion: string;
  persona_impacted: string | null;
}

// Matches backend StepSummary schema
export interface StepSummary {
  step_number: number;
  action_type: string;
  target: string | null;
  reasoning: string;
  friction_detected: string[];
  confidence: number;
  screenshot_url: string;
}

export interface ErrorClassification {
  error_type: "none" | "network" | "timeout" | "blocked" | "login_wall" | "safety" | "unknown";
  details: string;
  recoverable: boolean;
}

// Matches backend FrictionReport schema
export interface FrictionReport {
  session_id: string;
  url: string;
  goal: string;
  persona: string | null;
  status: string;
  total_steps: number;
  total_time_seconds: number;
  friction_items: FrictionItem[];
  friction_score: number;
  ux_risk_index: number;
  metrics: Record<string, number>;
  error_classification: ErrorClassification;
  executive_summary: string;
  improvement_priorities: string[];
  step_timeline: StepSummary[];
}
