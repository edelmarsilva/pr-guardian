from __future__ import annotations

from dataclasses import replace
from difflib import SequenceMatcher

from models import (
    Confidence,
    Finding,
    FindingPriority,
    PullRequest,
    Review,
    ReviewMetrics,
    Severity,
    VerificationResult,
    VerificationStatus,
)

from .context_builder import PullRequestContext


class DefaultReviewSynthesizer:
    """
    Consolidates specialized reviewer findings into the final PR review.

    Responsibilities:
    - attach verification results
    - remove refuted findings
    - suppress weak noise
    - deduplicate findings
    - classify blocking/advisory priority
    - produce final Review
    """

    WEAK_CONFIDENCES = {
        Confidence.POTENTIAL,
        Confidence.INFORMATIONAL,
    }

    BLOCKING_SEVERITIES = {
        Severity.CRITICAL,
        Severity.HIGH,
    }

    def synthesize(
        self,
        *,
        pull_request: PullRequest,
        context: PullRequestContext,
        findings: list[Finding],
        verifications: list[VerificationResult],
        reviewers_executed: list[str],
        metrics: ReviewMetrics,
    ) -> Review:
        working_findings = [
            self._copy_finding(finding)
            for finding in findings
        ]

        verification_map = {
            result.finding_id: result
            for result in verifications
        }

        for finding in working_findings:
            verification = verification_map.get(
                finding.id
            )

            if verification is not None:
                self._apply_verification(
                    finding,
                    verification,
                )

        non_refuted = [
            finding
            for finding in working_findings
            if finding.verification_status
            != VerificationStatus.REFUTED
        ]

        metrics.refuted_findings = (
            len(working_findings)
            - len(non_refuted)
        )

        deduplicated, duplicate_count = (
            self._deduplicate(
                non_refuted
            )
        )

        metrics.duplicate_findings_removed = (
            duplicate_count
        )

        publishable = []

        suppressed = 0

        for finding in deduplicated:
            if self._should_suppress(
                finding
            ):
                suppressed += 1
                continue

            finding.priority = (
                self._classify_priority(
                    finding
                )
            )

            publishable.append(
                finding
            )

        publishable = self._sort_findings(
            publishable
        )

        metrics.suppressed_findings = (
            suppressed
        )

        metrics.final_findings = len(
            publishable
        )

        metrics.blocking_findings = sum(
            1
            for finding in publishable
            if finding.priority
            == FindingPriority.BLOCKING
        )

        metrics.non_blocking_findings = sum(
            1
            for finding in publishable
            if finding.priority
            == FindingPriority.NON_BLOCKING
        )

        metrics.advisory_findings = sum(
            1
            for finding in publishable
            if finding.priority
            == FindingPriority.ADVISORY
        )

        summary = self._build_summary(
            pull_request=pull_request,
            context=context,
            findings=publishable,
            reviewers_executed=(
                reviewers_executed
            ),
            metrics=metrics,
        )

        return Review(
            pr_id=pull_request.identifier,
            summary=summary,
            findings=publishable,
            reviewers_executed=(
                reviewers_executed
            ),
            metrics=metrics.to_dict(),
            metadata={
                "base_sha": (
                    pull_request.base_sha
                ),
                "head_sha": (
                    pull_request.head_sha
                ),
                "risk_signals": (
                    context.risk_signals
                    if context is not None
                    else []
                ),
            },
        )

    @staticmethod
    def _copy_finding(
        finding: Finding,
    ) -> Finding:
        """
        Create a defensive copy so synthesis does not mutate the
        original reviewer artifact.
        """

        return replace(
            finding,
            evidence=list(
                finding.evidence
            ),
            metadata=dict(
                finding.metadata
            ),
        )

    @staticmethod
    def _apply_verification(
        finding: Finding,
        verification: VerificationResult,
    ) -> None:
        finding.verification_status = (
            verification.status
        )

        finding.metadata[
            "verification_method"
        ] = verification.method.value

        finding.metadata[
            "verification_notes"
        ] = verification.notes

        if verification.evidence:
            existing = set(
                finding.evidence
            )

            for evidence in (
                verification.evidence
            ):
                if evidence not in existing:
                    finding.evidence.append(
                        evidence
                    )
                    existing.add(
                        evidence
                    )

        if (
            verification.status
            == VerificationStatus.VERIFIED
        ):
            finding.confidence = (
                Confidence.CONFIRMED
            )

        elif (
            verification.status
            == VerificationStatus.REFUTED
        ):
            finding.metadata[
                "publishable"
            ] = False

    def _deduplicate(
        self,
        findings: list[Finding],
    ) -> tuple[
        list[Finding],
        int,
    ]:
        groups: list[
            list[Finding]
        ] = []

        for finding in findings:
            matched_group = None

            for group in groups:
                representative = group[0]

                if self._are_duplicates(
                    representative,
                    finding,
                ):
                    matched_group = group
                    break

            if matched_group is None:
                groups.append(
                    [finding]
                )
            else:
                matched_group.append(
                    finding
                )

        consolidated = [
            self._merge_group(group)
            for group in groups
        ]

        duplicate_count = (
            len(findings)
            - len(consolidated)
        )

        return (
            consolidated,
            duplicate_count,
        )

    def _are_duplicates(
        self,
        left: Finding,
        right: Finding,
    ) -> bool:
        if (
            left.file
            and right.file
            and left.file != right.file
        ):
            return False

        if (
            left.line is not None
            and right.line is not None
            and abs(
                left.line
                - right.line
            ) > 8
        ):
            return False

        category_match = (
            left.category
            == right.category
        )

        title_similarity = (
            self._similarity(
                left.title,
                right.title,
            )
        )

        description_similarity = (
            self._similarity(
                left.description,
                right.description,
            )
        )

        same_root_cause = (
            self._normalized_root_cause(
                left
            )
            == self._normalized_root_cause(
                right
            )
        )

        # Same root cause on the same file/line always deduplicate,
        # even if the categories differ (different reviewers may classify
        # the same underlying defect under different categories).
        if same_root_cause:
            return True

        return (
            category_match
            and (
                title_similarity >= 0.70
                or description_similarity >= 0.72
            )
        )

    def _merge_group(
        self,
        group: list[Finding],
    ) -> Finding:
        if len(group) == 1:
            finding = group[0]

            finding.metadata.setdefault(
                "source_findings",
                [finding.id],
            )

            return finding

        primary = sorted(
            group,
            key=self._finding_strength,
            reverse=True,
        )[0]

        merged = self._copy_finding(
            primary
        )

        source_findings = [
            finding.id
            for finding in group
        ]

        merged.metadata[
            "source_findings"
        ] = source_findings

        reviewers = sorted(
            {
                finding.reviewer
                for finding in group
                if finding.reviewer
            }
        )

        merged.metadata[
            "source_reviewers"
        ] = reviewers

        merged.evidence = (
            self._merge_evidence(
                group
            )
        )

        merged.severity = max(
            (
                finding.severity
                for finding in group
            ),
            key=self._severity_rank,
        )

        merged.confidence = max(
            (
                finding.confidence
                for finding in group
            ),
            key=self._confidence_rank,
        )

        merged.verification_status = (
            self._strongest_verification(
                group
            )
        )

        return merged

    def _should_suppress(
        self,
        finding: Finding,
    ) -> bool:
        if (
            finding.metadata.get(
                "publishable"
            )
            is False
        ):
            return True

        if (
            finding.severity
            == Severity.INFO
            and finding.confidence
            in self.WEAK_CONFIDENCES
        ):
            return True

        return (
            finding.severity == Severity.LOW
            and finding.confidence == Confidence.POTENTIAL
            and finding.verification_status == VerificationStatus.UNVERIFIED
        )

    def _classify_priority(
        self,
        finding: Finding,
    ) -> FindingPriority:
        if (
            finding.severity
            in self.BLOCKING_SEVERITIES
            and (
                finding.verification_status
                == VerificationStatus.VERIFIED
                or finding.confidence
                == Confidence.CONFIRMED
            )
        ):
            return (
                FindingPriority.BLOCKING
            )

        if finding.severity in {
            Severity.HIGH,
            Severity.MEDIUM,
        }:
            return (
                FindingPriority.NON_BLOCKING
            )

        return (
            FindingPriority.ADVISORY
        )

    def _sort_findings(
        self,
        findings: list[Finding],
    ) -> list[Finding]:
        return sorted(
            findings,
            key=lambda finding: (
                self._priority_rank(
                    finding.priority
                ),
                self._severity_rank(
                    finding.severity
                ),
                self._verification_rank(
                    finding.verification_status
                ),
                self._confidence_rank(
                    finding.confidence
                ),
            ),
            reverse=True,
        )

    def _build_summary(
        self,
        *,
        pull_request: PullRequest,
        context: PullRequestContext,
        findings: list[Finding],
        reviewers_executed: list[str],
        metrics: ReviewMetrics,
    ) -> str:
        blocking = [
            finding
            for finding in findings
            if finding.priority
            == FindingPriority.BLOCKING
        ]

        verified = [
            finding
            for finding in findings
            if finding.verification_status
            == VerificationStatus.VERIFIED
        ]

        affected_domains = (
            self._describe_domains(
                reviewers_executed
            )
        )

        lines = [
            (
                f"This Pull Request changes "
                f"{pull_request.changed_files_count or len(pull_request.changed_files)} "
                f"file(s)"
            )
        ]

        if affected_domains:
            lines[0] += (
                " and triggered review of "
                + ", ".join(
                    affected_domains
                )
                + "."
            )
        else:
            lines[0] += "."

        if blocking:
            lines.append(
                
                    f"{len(blocking)} blocking "
                    f"finding(s) remain."
                
            )
        else:
            lines.append(
                "No blocking findings remain after synthesis."
            )

        if verified:
            lines.append(
                
                    f"{len(verified)} final "
                    f"finding(s) were independently verified."
                
            )

        if metrics.refuted_findings:
            lines.append(
                
                    f"{metrics.refuted_findings} "
                    f"finding(s) were refuted "
                    f"during verification."
                
            )

        if (
            metrics.duplicate_findings_removed
        ):
            lines.append(
                
                    f"{metrics.duplicate_findings_removed} "
                    f"duplicate finding(s) were "
                    f"consolidated."
                
            )

        if context is not None and context.risk_signals:
            lines.append(
                
                    "Detected change signals: "
                    + ", ".join(
                        context.risk_signals
                    )
                    + "."
                
            )

        return " ".join(
            lines
        )

    @staticmethod
    def _describe_domains(
        reviewers: list[str],
    ) -> list[str]:
        mapping = {
            "code-review": "application logic",
            "security-review": "security",
            "test-impact": "test impact",
            "architecture-review": "architecture",
            "database-review": "database behavior",
            "api-review": "API contracts",
            "queue-review": "asynchronous processing",
        }

        return [
            mapping.get(
                reviewer,
                reviewer,
            )
            for reviewer in reviewers
        ]

    @staticmethod
    def _merge_evidence(
        group: list[Finding],
    ) -> list[str]:
        seen: set[str] = set()
        merged: list[str] = []

        for finding in group:
            for item in finding.evidence:
                if item in seen:
                    continue

                seen.add(
                    item
                )

                merged.append(
                    item
                )

        return merged

    @staticmethod
    def _normalized_root_cause(
        finding: Finding,
    ) -> str:
        root_cause = finding.metadata.get(
            "root_cause"
        )

        if root_cause:
            return str(
                root_cause
            ).strip().lower()

        return ""

    @staticmethod
    def _similarity(
        left: str,
        right: str,
    ) -> float:
        return SequenceMatcher(
            None,
            left.lower().strip(),
            right.lower().strip(),
        ).ratio()

    @staticmethod
    def _severity_rank(
        severity: Severity,
    ) -> int:
        return {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }[severity]

    @staticmethod
    def _confidence_rank(
        confidence: Confidence,
    ) -> int:
        return {
            Confidence.INFORMATIONAL: 0,
            Confidence.POTENTIAL: 1,
            Confidence.LIKELY: 2,
            Confidence.CONFIRMED: 3,
        }[confidence]

    @staticmethod
    def _verification_rank(
        status: VerificationStatus,
    ) -> int:
        return {
            VerificationStatus.REFUTED: 0,
            VerificationStatus.VERIFICATION_FAILED: 1,
            VerificationStatus.UNVERIFIED: 2,
            VerificationStatus.NOT_APPLICABLE: 3,
            VerificationStatus.VERIFIED: 4,
        }[status]

    @staticmethod
    def _priority_rank(
        priority: FindingPriority | None,
    ) -> int:
        return {
            None: 0,
            FindingPriority.ADVISORY: 1,
            FindingPriority.NON_BLOCKING: 2,
            FindingPriority.BLOCKING: 3,
        }[priority]

    def _finding_strength(
        self,
        finding: Finding,
    ) -> tuple[int, int, int]:
        return (
            self._severity_rank(
                finding.severity
            ),
            self._verification_rank(
                finding.verification_status
            ),
            self._confidence_rank(
                finding.confidence
            ),
        )

    def _strongest_verification(
        self,
        group: list[Finding],
    ) -> VerificationStatus:
        return max(
            (
                finding.verification_status
                for finding in group
            ),
            key=self._verification_rank,
        )
