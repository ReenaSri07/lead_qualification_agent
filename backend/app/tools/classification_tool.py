"""
Lead Classification Tool.
Classifies leads as HOT, NURTURE, or DISQUALIFY based on their score.
Each decision includes reason, evidence, and confidence.
"""
from typing import Dict, Any


class LeadClassificationTool:
    """
    Classifies leads into categories based on their score.
    HOT: score >= 80
    NURTURE: score 50-79
    DISQUALIFY: score < 50
    """

    def classify(self, scoring_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a lead based on scoring results.

        Args:
            scoring_result: Dictionary with total_score, dimension_scores, reasoning, evidence

        Returns:
            Dictionary with classification, reason, evidence, and confidence
        """
        total_score = scoring_result.get("total_score", 0)
        reasoning = scoring_result.get("reasoning", "No reasoning provided")
        evidence = scoring_result.get("evidence", "No evidence provided")

        if total_score >= 80:
            classification = "HOT"
            reason = (
                f"Lead scored {total_score}/100, exceeding the HOT threshold of 80. "
                f"The lead demonstrates strong company fit, role alignment, and buying intent. "
                f"Recommended for immediate outreach."
            )
            confidence = min(100, total_score)  # Confidence scales with score
        elif total_score >= 50:
            classification = "NURTURE"
            reason = (
                f"Lead scored {total_score}/100, placing in the NURTURE range (50-79). "
                f"The lead shows potential but needs further engagement and education "
                f"before being ready for direct sales outreach."
            )
            confidence = min(80, total_score)
        else:
            classification = "DISQUALIFY"
            reason = (
                f"Lead scored {total_score}/100, below the NURTURE threshold of 50. "
                f"The lead does not meet the minimum criteria for the Ideal Customer Profile. "
                f"Recommended for archiving."
            )
            confidence = max(60, 100 - total_score)  # Higher confidence for low scores

        return {
            "classification": classification,
            "reason": reason,
            "evidence": evidence,
            "confidence": confidence,
            "score": total_score,
        }