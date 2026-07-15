"""
Lead Scoring Tool.
Implements identity-blind scoring that removes personal identifiers before scoring.
Only company signals influence the score for fairness.
Uses LLM enrichment when available, with rule-based fallback scoring.
"""
from typing import Dict, Any, List
from app.llm_client import LLMClient


class LeadScoringTool:
    """
    Scores leads from 0-100 based on company fit, role fit, buying intent,
    technology match, budget indicators, urgency, decision maker authority,
    and recent activity. Implements identity-blind scoring.
    Has a rule-based fallback when LLM is unavailable.
    """

    DECISION_MAKER_SCORES = {
        "CEO": 100, "CTO": 100, "CFO": 100, "COO": 100, "C-Level": 100,
        "Chief": 100, "President": 100, "Founder": 95, "Owner": 95,
        "VP": 85, "Vice President": 85, "Head of": 80,
        "Director": 70, "Senior Director": 75,
        "Manager": 50, "Senior Manager": 55,
        "Individual": 30, "Unknown": 30,
    }

    BUYING_SIGNAL_KEYWORDS = [
        "looking for", "interested in", "evaluating", "considering",
        "need", "solution", "pilot", "trial", "budget", "purchase",
        "implementing", "scaling", "growing", "expand", "upgrade",
        "migrate", "improve", "optimize", "automate", "integrate",
        "ai", "machine learning", "data", "analytics",
        "deployment", "rollout", "adopting", "procurement",
        "vendor", "partnership", "collaboration",
    ]

    HIGH_INTENT_SIGNALS = [
        "budget approved", "budget allocated", "approved budget",
        "q1", "q2", "q3", "q4", "this quarter", "next quarter",
        "immediately", "urgent", "asap", "deployment", "poc",
        "proof of concept", "pilot program", "enterprise agreement",
        "contract", "vendor evaluation", "rfp", "request for proposal",
    ]

    TECH_SIGNALS = [
        "python", "javascript", "typescript", "react", "node",
        "aws", "azure", "gcp", "cloud", "kubernetes", "docker",
        "api", "microservices", "saas", "enterprise",
        "ai", "ml", "machine learning", "deep learning",
        "data pipeline", "data warehouse", "big data",
    ]

    INDUSTRY_PREFERRED = [
        "technology", "software", "saas", "fintech", "healthtech",
        "ai", "machine learning", "data", "cloud", "cybersecurity",
        "e-commerce", "enterprise", "analytics", "biotech",
    ]

    def __init__(self):
        self.llm = LLMClient()

    def strip_identity(self, enriched_profile: Dict[str, Any]) -> Dict[str, Any]:
        identity_blind = {
            "company": enriched_profile.get("company", "Unknown"),
            "industry": enriched_profile.get("industry", "Unknown"),
            "company_size": enriched_profile.get("company_size", "Unknown"),
            "employee_count": enriched_profile.get("employee_count", "Unknown"),
            "revenue": enriched_profile.get("revenue", "Unknown"),
            "role": enriched_profile.get("role", "Unknown"),
            "job_title": enriched_profile.get("job_title", "Unknown"),
            "location": enriched_profile.get("location", "Unknown"),
            "buying_signals": enriched_profile.get("buying_signals", []),
            "website": enriched_profile.get("website", "Unknown"),
            "technology_stack": enriched_profile.get("technology_stack", []),
            "funding": enriched_profile.get("funding", "Unknown"),
            "recent_news": enriched_profile.get("recent_news", "Unknown"),
            "decision_maker_level": enriched_profile.get("decision_maker_level", "Unknown"),
            "notes": enriched_profile.get("notes", ""),
            "source": enriched_profile.get("source", ""),
        }
        return identity_blind

    def _detect_role_fit(self, combined_role: str) -> int:
        """Detect role fit score from combined role text."""
        combined_lower = combined_role.lower()

        # C-Suite / Executive
        if any(t in combined_lower for t in ["ceo", "cto", "cfo", "coo", "chief", "president", "founder", "owner"]):
            return 95
        # VP / Head
        if any(t in combined_lower for t in ["vp ", "vice president", "vice-president", "head of", "head "]):
            return 85
        # Director
        if "director" in combined_lower and "managing director" not in combined_lower:
            return 70
        # Senior Manager
        if "senior manager" in combined_lower or "sr. manager" in combined_lower:
            return 60
        # Manager
        if "manager" in combined_lower:
            return 55
        # Engineer / Developer
        if any(t in combined_lower for t in ["engineer", "developer", "architect", "lead"]):
            return 50
        # Analyst
        if "analyst" in combined_lower or "specialist" in combined_lower:
            return 35
        return 30

    def _detect_buying_intent(self, signal_text: str) -> int:
        """Detect buying intent from signal text."""
        if not signal_text:
            return 20

        signal_lower = signal_text.lower()

        # High intent signals
        high_intent_count = 0
        for signal in self.HIGH_INTENT_SIGNALS:
            if signal in signal_lower:
                high_intent_count += 1

        # Medium intent signals
        medium_intent_count = 0
        for keyword in self.BUYING_SIGNAL_KEYWORDS:
            if keyword in signal_lower:
                medium_intent_count += 1

        # Score calculation
        if high_intent_count >= 3:
            return 95
        elif high_intent_count >= 2:
            return 85
        elif high_intent_count >= 1:
            return 75
        elif medium_intent_count >= 5:
            return 70
        elif medium_intent_count >= 3:
            return 60
        elif medium_intent_count >= 1:
            return 50
        return 20

    def _detect_urgency(self, signal_text: str) -> int:
        """Detect urgency from signal text."""
        if not signal_text:
            return 20

        signal_lower = signal_text.lower()
        urgent_signals = [
            "immediately", "urgent", "asap", "now", "soon",
            "this quarter", "q1", "q2", "q3", "q4",
            "deployment", "rollout", "poc", "proof of concept",
            "pilot", "evaluating", "decision",
        ]

        urgency_count = 0
        for signal in urgent_signals:
            if signal in signal_lower:
                urgency_count += 1

        if urgency_count >= 3:
            return 85
        elif urgency_count >= 2:
            return 70
        elif urgency_count >= 1:
            return 55
        return 20

    def _detect_budget(self, signal_text: str) -> int:
        """Detect budget indicators from signal text."""
        if not signal_text:
            return 20

        signal_lower = signal_text.lower()
        budget_signals = [
            "budget", "approved", "allocated", "funding",
            "investment", "spend", "purchase", "procurement",
            "enterprise", "contract", "million", "revenue",
        ]

        budget_count = 0
        for signal in budget_signals:
            if signal in signal_lower:
                budget_count += 1

        if budget_count >= 3:
            return 90
        elif budget_count >= 2:
            return 75
        elif budget_count >= 1:
            return 60
        return 20

    def _rule_based_score(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced rule-based scoring that can reach HOT threshold.
        """
        role = str(profile.get("role", "Unknown")).strip()
        job_title = str(profile.get("job_title", "Unknown")).strip()
        industry = str(profile.get("industry", "Unknown")).strip()
        buying_signals = profile.get("buying_signals", [])
        tech_stack = profile.get("technology_stack", [])
        decision_maker = str(profile.get("decision_maker_level", "Unknown")).strip()
        funding = str(profile.get("funding", "Unknown")).strip()
        company = str(profile.get("company", "Unknown")).strip()
        notes = str(profile.get("notes", "")).strip()
        source = str(profile.get("source", "")).strip()

        # Build combined signal text from all sources
        signal_text = " ".join([
            " ".join([str(s).lower() for s in buying_signals]),
            notes.lower(),
            source.lower(),
        ])

        # Combined role for matching
        role_lower = role.lower()
        title_lower = job_title.lower()
        combined_role = f"{role_lower} {title_lower}"

        # Company Fit (0-100)
        company_fit = 40  # Default baseline
        if company and company != "Unknown":
            company_fit = 50  # Known company
        for ind in self.INDUSTRY_PREFERRED:
            if ind in industry.lower():
                company_fit = 85
                break
        # Check if company name suggests tech
        if any(ind in company.lower() for ind in self.INDUSTRY_PREFERRED):
            company_fit = max(company_fit, 80)
        if "ai" in company.lower() or "tech" in company.lower() or "data" in company.lower() or "cloud" in company.lower():
            company_fit = max(company_fit, 85)
        if source and ("tech" in source.lower() or "ai" in source.lower() or ".com" in source.lower()):
            company_fit = max(company_fit, 65)

        # Role Fit (0-100)
        role_fit = self._detect_role_fit(combined_role)

        # Buying Intent (0-100)
        buying_intent = self._detect_buying_intent(signal_text)

        # Technology Match (0-100)
        tech_match = 20
        tech_text = " ".join([str(t).lower() for t in tech_stack])
        tech_found = 0
        for signal in self.TECH_SIGNALS:
            if signal in tech_text or signal in signal_text:
                tech_found += 1
        if tech_found >= 5:
            tech_match = 90
        elif tech_found >= 3:
            tech_match = 75
        elif tech_found >= 1:
            tech_match = 60
        elif "ai" in signal_text or "analytics" in signal_text or "ml" in signal_text:
            tech_match = 55

        # Budget Indicators (0-100)
        budget_indicators = self._detect_budget(signal_text)
        if funding and funding != "Unknown" and ("million" in funding.lower() or "series" in funding.lower()):
            budget_indicators = max(budget_indicators, 85)
        if "enterprise" in industry.lower() or "enterprise" in signal_text:
            budget_indicators = max(budget_indicators, 70)

        # Urgency (0-100)
        urgency = self._detect_urgency(signal_text)

        # Decision Maker Authority (0-100)
        dm_authority = self.DECISION_MAKER_SCORES.get(decision_maker, 30)
        for key, score in self.DECISION_MAKER_SCORES.items():
            if key.lower() in combined_role:
                dm_authority = max(dm_authority, score)

        # Recent Activity (0-100)
        recent_activity = 20
        if funding and funding != "Unknown":
            recent_activity = 65
        news = str(profile.get("recent_news", "")).lower()
        if "funding" in news or "expansion" in news or "hiring" in news or "launch" in news:
            recent_activity = 75
        if "growing" in signal_text or "scaling" in signal_text or "expand" in signal_text:
            recent_activity = max(recent_activity, 60)
        if "evaluating" in signal_text or "deployment" in signal_text or "implementing" in signal_text:
            recent_activity = max(recent_activity, 55)

        # Optimized weights to emphasize strong signals
        weights = {
            "company_fit": 0.15,
            "role_fit": 0.20,
            "buying_intent": 0.20,
            "technology_match": 0.10,
            "budget_indicators": 0.10,
            "urgency": 0.10,
            "decision_maker_authority": 0.10,
            "recent_activity": 0.05,
        }

        dimension_scores = {
            "company_fit": company_fit,
            "role_fit": role_fit,
            "buying_intent": buying_intent,
            "technology_match": tech_match,
            "budget_indicators": budget_indicators,
            "urgency": urgency,
            "decision_maker_authority": dm_authority,
            "recent_activity": recent_activity,
        }

        total_score = sum(
            dimension_scores[dim] * weight
            for dim, weight in weights.items()
        )
        total_score = round(total_score, 1)

        # Build evidence
        evidence_parts = []
        if company_fit >= 70:
            evidence_parts.append(f"Strong company fit in target industry: {industry}")
        if role_fit >= 70:
            evidence_parts.append(f"Senior decision-maker role: {role}")
        if buying_intent >= 60:
            evidence_parts.append(f"Strong buying signals detected")
        if tech_match >= 60:
            evidence_parts.append(f"Technology alignment with our solution")
        if budget_indicators >= 60:
            evidence_parts.append(f"Budget indicators present")
        if urgency >= 60:
            evidence_parts.append(f"Time-sensitive engagement signals")
        if dm_authority >= 70:
            evidence_parts.append(f"Decision maker authority confirmed")

        reasoning = f"Lead scored {total_score}/100. "
        if evidence_parts:
            reasoning += " | ".join(evidence_parts)

        return {
            "total_score": total_score,
            "dimension_scores": dimension_scores,
            "reasoning": reasoning,
            "evidence": "; ".join(evidence_parts) if evidence_parts else "Limited data available for scoring",
        }

    def _build_scoring_prompt(self, profile: Dict[str, Any]) -> str:
        return f"""
You are a lead scoring specialist. Score this lead based ONLY on company and professional signals.
Personal identity information has been removed to ensure fair scoring.

IDENTITY-BLIND PROFILE:
- Company: {profile.get('company', 'Unknown')}
- Industry: {profile.get('industry', 'Unknown')}
- Company Size: {profile.get('company_size', 'Unknown')}
- Employee Count: {profile.get('employee_count', 'Unknown')}
- Revenue: {profile.get('revenue', 'Unknown')}
- Role: {profile.get('role', 'Unknown')}
- Job Title: {profile.get('job_title', 'Unknown')}
- Location: {profile.get('location', 'Unknown')}
- Buying Signals: {profile.get('buying_signals', [])}
- Website: {profile.get('website', 'Unknown')}
- Technology Stack: {profile.get('technology_stack', [])}
- Funding: {profile.get('funding', 'Unknown')}
- Recent News: {profile.get('recent_news', 'Unknown')}
- Decision Maker Level: {profile.get('decision_maker_level', 'Unknown')}

SCORING DIMENSIONS (each 0-100):
1. Company Fit: How well does the company match ideal customer profile?
2. Role Fit: How relevant is the contact's role for purchasing decisions?
3. Buying Intent: Evidence of active buying signals or pain points?
4. Technology Match: Does their tech stack align with our solution?
5. Budget Indicators: Signs of budget availability or investment?
6. Urgency: Time sensitivity of their need?
7. Decision Maker Authority: Is this person a decision maker?
8. Recent Activity: Recent funding, news, hiring, or expansion?

Return a JSON object:
{{
    "total_score": 0-100,
    "dimension_scores": {{
        "company_fit": 0-100,
        "role_fit": 0-100,
        "buying_intent": 0-100,
        "technology_match": 0-100,
        "budget_indicators": 0-100,
        "urgency": 0-100,
        "decision_maker_authority": 0-100,
        "recent_activity": 0-100
    }},
    "reasoning": "Detailed explanation of the score",
    "evidence": "Specific evidence from the profile supporting the score"
}}
"""

    def score(self, enriched_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a lead based on their enriched profile.
        Implements identity-blind scoring for fairness.
        Falls back to rule-based scoring if LLM is unavailable.
        """
        # Step 1: Strip identity information
        identity_blind_profile = self.strip_identity(enriched_profile)

        # Check if we have enough data for meaningful scoring
        has_data = any(
            v != "Unknown" and v != [] and v is not None
            for v in identity_blind_profile.values()
        )

        if not has_data:
            return self._rule_based_score(identity_blind_profile)

        # Step 2: Try LLM-based scoring
        prompt = self._build_scoring_prompt(identity_blind_profile)
        result = self.llm.call_json(
            system_prompt="You are a lead scoring specialist. Score leads fairly based only on company and professional signals. Never consider personal identity factors.",
            user_prompt=prompt,
            temperature=0.1,
        )

        if result["success"]:
            scoring = result["parsed"]

            if "total_score" not in scoring:
                scoring["total_score"] = 0
            if "dimension_scores" not in scoring:
                scoring["dimension_scores"] = {}
            if "reasoning" not in scoring:
                scoring["reasoning"] = "No reasoning provided"
            if "evidence" not in scoring:
                scoring["evidence"] = "No evidence provided"

            default_dimensions = {
                "company_fit": 0, "role_fit": 0, "buying_intent": 0,
                "technology_match": 0, "budget_indicators": 0,
                "urgency": 0, "decision_maker_authority": 0, "recent_activity": 0,
            }
            for dim, default_val in default_dimensions.items():
                if dim not in scoring["dimension_scores"]:
                    scoring["dimension_scores"][dim] = default_val

            scoring["total_score"] = max(0, min(100, float(scoring["total_score"])))
            for dim in scoring["dimension_scores"]:
                scoring["dimension_scores"][dim] = max(0, min(100, float(scoring["dimension_scores"][dim])))

            return scoring

        # Step 3: Fallback to rule-based scoring
        return self._rule_based_score(identity_blind_profile)