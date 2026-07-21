"""Build semantic ImplementationPreview objects from plan recommendations.

Product boundary (R3):
  Preview explains implementation intent — never emits patches, diffs, or writes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from psa.core.pipeline import Audit
    from psa.findings import Finding
    from psa.recommend.graph import PlanRecommendation


@dataclass(frozen=True)
class ActionGroup:
    """Labeled or unlabeled action list for one file."""

    label: str  # empty => bullets only
    items: tuple[str, ...]


@dataclass(frozen=True)
class FileActions:
    path: str
    purpose: str
    groups: tuple[ActionGroup, ...]

    @property
    def actions(self) -> tuple[str, ...]:
        return tuple(item for g in self.groups for item in g.items)


@dataclass(frozen=True)
class ImplementationPreview:
    step: int
    title: str
    effort: str
    overview: str
    intent: str
    primary_change: str
    file_actions: tuple[FileActions, ...]
    result: tuple[str, ...]
    files_modified: tuple[str, ...]
    files_added: tuple[str, ...]
    files_removed: tuple[str, ...]
    impact_lines: tuple[str, ...]

    @property
    def action_count(self) -> int:
        return sum(len(fa.actions) for fa in self.file_actions)

    @property
    def files_affected(self) -> int:
        return len(
            set(self.files_modified) | set(self.files_added) | set(self.files_removed)
        )


@dataclass(frozen=True)
class PreviewSet:
    steps: tuple[ImplementationPreview, ...]
    expected_status: str
    repository_impact: tuple[str, ...]

    @property
    def files_modified(self) -> tuple[str, ...]:
        paths: set[str] = set()
        for s in self.steps:
            paths.update(s.files_modified)
        return tuple(sorted(paths))

    @property
    def files_added(self) -> tuple[str, ...]:
        paths: set[str] = set()
        for s in self.steps:
            paths.update(s.files_added)
        return tuple(sorted(paths))

    @property
    def files_removed(self) -> tuple[str, ...]:
        paths: set[str] = set()
        for s in self.steps:
            paths.update(s.files_removed)
        return tuple(sorted(paths))

    @property
    def files_affected(self) -> int:
        return len(
            set(self.files_modified) | set(self.files_added) | set(self.files_removed)
        )


# Semantic templates — architectural actions, not line edits.
_RULE_TEMPLATE: dict[str, dict] = {
    "DUP001": {
        "intent": (
            "Consolidate duplicated architectural guidance into a single "
            "authoritative location while preserving repository behaviour."
        ),
        "primary_change": "Consolidate duplicate instructions",
        "impact": (
            "Duplicate architectural guidance will be consolidated "
            "into a single authoritative source."
        ),
        "result": (
            "Single authoritative instruction source established.",
            "Duplicate guidance removed.",
            "Repository behaviour preserved.",
        ),
    },
    "ACT002": {
        "intent": (
            "Add explicit activation frontmatter so Cursor can decide when "
            "each rule should apply."
        ),
        "primary_change": "Enable rule activation",
        "impact": (
            "Cursor rules will gain explicit activation metadata "
            "to ensure predictable activation."
        ),
        "result": (
            "Activation frontmatter present on targeted rules.",
            "Rules become selectable by the editor.",
        ),
    },
    "ACT001": {
        "intent": (
            "Review dormant rules and either activate them with clear intent "
            "or remove obsolete guidance."
        ),
        "primary_change": "Activate or remove unused rules",
        "impact": "Dormant rules will either be activated or removed.",
        "result": (
            "Dormant rules reviewed.",
            "Only intentional rules remain in the prompt surface.",
        ),
    },
    "STYLE001": {
        "intent": (
            "Separate volatile worklog content from durable instructions so "
            "the stable prefix stays clean."
        ),
        "primary_change": "Separate worklog from durable instructions",
        "impact": "Worklog content will be separated from durable instructions.",
        "result": (
            "Durable instructions remain in the stable prefix.",
            "Volatile worklog content no longer poisons early context.",
        ),
    },
    "ORDER001": {
        "intent": (
            "Move volatile sections below stable guidance so prompt-prefix "
            "reuse remains effective."
        ),
        "primary_change": "Reorder volatile sections below stable guidance",
        "impact": "Volatile sections will move below stable guidance.",
        "result": (
            "Stable guidance remains at the front of the file.",
            "Volatile sections no longer break prefix reuse.",
        ),
    },
}

_DEFAULT_TEMPLATE = {
    "intent": "Address related prompt-architecture findings while preserving repository behaviour.",
    "primary_change": "Address related findings",
    "impact": "Related prompt-architecture findings will be addressed.",
    "result": (
        "Targeted findings resolved.",
        "Repository behaviour preserved.",
    ),
}


def build_preview_set(audit: Audit) -> PreviewSet:
    plan = getattr(audit.dependency_graph, "plan", ()) or ()
    findings_by_id = {f.id: f for f in audit.findings}
    steps: list[ImplementationPreview] = []
    for i, rec in enumerate(plan, 1):
        steps.append(_preview_for_step(i, rec, findings_by_id))

    if not steps:
        return PreviewSet(
            steps=(),
            expected_status="Healthy",
            repository_impact=(
                "No implementation changes are planned.",
                "Repository behaviour is expected to remain unchanged.",
            ),
        )

    impact: list[str] = []
    seen: set[str] = set()
    for s in steps:
        for line in s.impact_lines:
            if line not in seen:
                seen.add(line)
                impact.append(line)
    impact.append("No new instruction sources will be introduced.")
    impact.append("Repository behaviour is expected to remain unchanged.")

    return PreviewSet(
        steps=tuple(steps),
        expected_status="Healthy",
        repository_impact=tuple(impact),
    )


def get_step_preview(audit: Audit, step: int) -> ImplementationPreview:
    preview = build_preview_set(audit)
    if step < 1 or step > len(preview.steps):
        n = len(preview.steps)
        raise ValueError(
            f"Invalid step {step}: plan has {n} recommendation"
            f"{'' if n == 1 else 's'}."
        )
    return preview.steps[step - 1]


def _preview_for_step(
    step: int,
    rec: PlanRecommendation,
    findings_by_id: dict[str, Finding],
) -> ImplementationPreview:
    rule = rec.rule_ids[0] if rec.rule_ids else ""
    tmpl = _RULE_TEMPLATE.get(rule, _DEFAULT_TEMPLATE)
    paths = _paths_for_rec(rec, findings_by_id)
    file_actions = _file_actions_for(rule, paths, rec, findings_by_id)
    modified = tuple(fa.path for fa in file_actions)
    n_files = len(modified)

    return ImplementationPreview(
        step=step,
        title=rec.title,
        effort=rec.estimated_effort,
        overview=_overview_for(rule, n_files, modified),
        intent=str(tmpl["intent"]),
        primary_change=str(tmpl["primary_change"]),
        file_actions=file_actions,
        result=tuple(tmpl["result"]),
        files_modified=modified,
        files_added=(),
        files_removed=(),
        impact_lines=(str(tmpl["impact"]),),
    )


def _overview_for(rule: str, n_files: int, paths: tuple[str, ...]) -> str:
    n = n_files if n_files else 1
    files_word = "file" if n == 1 else "files"
    cursor_rules = bool(paths) and all(
        p.startswith(".cursor/rules/") or "/.cursor/rules/" in p for p in paths
    )
    kind = "Cursor rule files" if cursor_rules and n > 1 else (
        "Cursor rule file" if cursor_rules else files_word
    )
    if cursor_rules and n > 1:
        count_kind = f"{n} Cursor rule files"
    elif cursor_rules:
        count_kind = "1 Cursor rule file"
    else:
        count_kind = f"{n} {files_word}"

    if rule == "DUP001":
        return (
            f"This recommendation consolidates duplicated architectural guidance "
            f"across {count_kind} by retaining a single authoritative source and "
            f"removing duplicated instructions elsewhere."
        )
    if rule == "ACT002":
        return (
            f"This recommendation adds activation frontmatter to {count_kind} "
            f"so Cursor can decide when each rule should apply."
        )
    if rule == "ACT001":
        return (
            f"This recommendation reviews {count_kind} with dormant activation "
            f"and either activates them with clear intent or removes obsolete guidance."
        )
    if rule == "STYLE001":
        return (
            f"This recommendation separates volatile worklog content from durable "
            f"instructions in {count_kind}."
        )
    if rule == "ORDER001":
        return (
            f"This recommendation moves volatile sections below stable guidance "
            f"in {count_kind} so prompt-prefix reuse remains effective."
        )
    return (
        f"This recommendation addresses related prompt-architecture findings "
        f"across {count_kind}."
    )


def _paths_for_rec(
    rec: PlanRecommendation,
    findings_by_id: dict[str, Finding],
) -> tuple[str, ...]:
    paths: set[str] = set()
    for fid in rec.addresses:
        finding = findings_by_id.get(fid)
        if not finding:
            continue
        for ev in finding.evidence:
            if ev.path:
                paths.add(ev.path.replace("\\", "/"))
    return tuple(sorted(paths))


def _file_actions_for(
    rule: str,
    paths: tuple[str, ...],
    rec: PlanRecommendation,
    findings_by_id: dict[str, Finding],
) -> tuple[FileActions, ...]:
    if not paths:
        return (
            FileActions(
                path="(target files from recommendation evidence)",
                purpose="Apply the planned remediation for this recommendation.",
                groups=(
                    ActionGroup(
                        "",
                        ("Apply the planned remediation for this recommendation.",),
                    ),
                ),
            ),
        )

    if rule == "DUP001":
        return _dup_actions(paths, rec, findings_by_id)
    if rule == "ACT002":
        return tuple(
            FileActions(
                path=p,
                purpose="Enable predictable rule activation for this file.",
                groups=(
                    ActionGroup(
                        "",
                        (
                            "Add activation frontmatter.",
                            "Add description metadata.",
                        ),
                    ),
                ),
            )
            for p in paths
        )
    if rule == "ACT001":
        return tuple(
            FileActions(
                path=p,
                purpose="Resolve dormant activation for this rule.",
                groups=(
                    ActionGroup(
                        "",
                        (
                            "Review dormant activation intent.",
                            "Activate the rule or remove obsolete guidance.",
                        ),
                    ),
                ),
            )
            for p in paths
        )
    if rule == "STYLE001":
        return tuple(
            FileActions(
                path=p,
                purpose="Keep durable instructions in the stable prefix.",
                groups=(
                    ActionGroup(
                        "",
                        (
                            "Separate worklog content from durable instructions.",
                            "Relocate volatile worklog content out of the stable prefix.",
                        ),
                    ),
                ),
            )
            for p in paths
        )
    if rule == "ORDER001":
        return tuple(
            FileActions(
                path=p,
                purpose="Restore stable-first ordering in this instruction file.",
                groups=(
                    ActionGroup(
                        "",
                        (
                            "Move volatile sections below stable guidance.",
                            "Preserve instruction ordering within the stable prefix.",
                        ),
                    ),
                ),
            )
            for p in paths
        )
    return tuple(
        FileActions(
            path=p,
            purpose="Apply the planned remediation for this file.",
            groups=(
                ActionGroup(
                    "",
                    ("Apply the planned remediation for this recommendation.",),
                ),
            ),
        )
        for p in paths
    )


def _dup_actions(
    paths: tuple[str, ...],
    rec: PlanRecommendation,
    findings_by_id: dict[str, Finding],
) -> tuple[FileActions, ...]:
    """First path is canonical; others lose duplicated guidance."""
    excerpts = _dup_excerpts(rec, findings_by_id)
    canonical = paths[0]
    others = paths[1:] if len(paths) > 1 else ()

    if not others:
        return (
            FileActions(
                path=canonical,
                purpose="Merge duplicated instruction sections into one authoritative copy.",
                groups=(
                    ActionGroup(
                        "",
                        (
                            "Merge duplicated instruction sections.",
                            "Retain a single authoritative copy.",
                            "Preserve instruction ordering.",
                        ),
                    ),
                ),
            ),
        )

    out: list[FileActions] = [
        FileActions(
            path=canonical,
            purpose="Retain the canonical architectural guidance.",
            groups=(
                ActionGroup(
                    "",
                    (
                        "Preserve instruction ordering.",
                        "Update references to the canonical guidance.",
                    ),
                ),
            ),
        )
    ]
    for p in others:
        if excerpts:
            groups = (
                ActionGroup("Remove duplicated instructions", excerpts),
            )
        else:
            groups = (
                ActionGroup(
                    "",
                    ("Remove duplicated instruction sections.",),
                ),
            )
        out.append(
            FileActions(
                path=p,
                purpose="Remove duplicated architectural guidance.",
                groups=groups,
            )
        )
    return tuple(out)


def _dup_excerpts(
    rec: PlanRecommendation,
    findings_by_id: dict[str, Finding],
) -> tuple[str, ...]:
    found: list[str] = []
    seen: set[str] = set()
    for fid in rec.addresses:
        finding = findings_by_id.get(fid)
        if not finding:
            continue
        for ev in finding.evidence:
            text = (ev.excerpt or "").strip()
            if not text:
                continue
            one = " ".join(text.split())
            if len(one) > 72:
                one = one[:69].rstrip() + "..."
            # Strip surrounding quotes for grouped list presentation
            if len(one) >= 2 and one[0] == one[-1] and one[0] in "\"'":
                one = one[1:-1]
            if one not in seen:
                seen.add(one)
                found.append(one)
            if len(found) >= 3:
                return tuple(found)
    return tuple(found)
