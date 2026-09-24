import math


class RiskEngine:
    def _level_from_score(self, score):
        if score < 2.5:
            return "LOW"
        if score < 5.0:
            return "MID"
        if score < 8.0:
            return "HIGH"
        return "CRITICAL"

    def _normalize_volume_score(self, total_rows):
        return min(math.log10(total_rows + 1), 4.0)

    def _normalize_size_penalty(self, largest_size):
        return min(largest_size / 5_000_000, 4.0)

    # SYSTEM LEVEL
    def compute(self, dep_metrics, size_metrics, tables_metadata):
        dependency_score = min(dep_metrics.get("total_dependencies", 0), 4.0)

        total_rows = size_metrics.get("total_rows", 0)
        volume_score = self._normalize_volume_score(total_rows)

        largest_size = size_metrics.get("largest_table_size_bytes", 0)
        size_penalty = self._normalize_size_penalty(largest_size)

        score = (
            0.4 * dependency_score +
            0.35 * volume_score +
            0.25 * size_penalty
        )
        score = round(score, 2)

        return {
            "risk_score": score,
            "risk_level": self._level_from_score(score)
        }

    # ROW LEVEL
    def calculate_risk(self, dependency_score, volume_score, size_penalty):
        score = (
            0.4 * min(dependency_score, 4.0) +
            0.35 * min(volume_score, 4.0) +
            0.25 * min(size_penalty, 4.0)
        )

        return self._level_from_score(round(score, 2))

    def evaluate(self, data):

        for row in data:
            row["risk_status"] = self.calculate_risk(
                row["dependency_score"],
                row["volume_score"],
                row["size_penalty"]
            )

        return data
