"""Graph correctness tests for read-only scientific stacked PR audits."""
from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.audit_scientific_pr_stack import audit_open_prs, markdown_summary


def pr(n: int, head: str, base: str, draft=True):
    return {
        "number": n,
        "title": f"Scoped research work #{n}",
        "head": {"ref": head, "repo": {"full_name": "carlers/quantum-opt-dashboard"}},
        "base": {"ref": base, "repo": {"full_name": "carlers/quantum-opt-dashboard"}},
        "draft": draft,
        "state": "open",
        "html_url": f"https://github.com/carlers/quantum-opt-dashboard/pull/{n}",
    }


def graph():
    # Deliberately out of order, with two independent main-based PR streams.
    return [
        pr(11, "science-trace", "science-reference"),
        pr(31, "policy-research", "main"),
        pr(12, "science-reference", "main"),
        pr(13, "science-math-runtime", "science-trace"),
    ]


class ScientificStackGraphTests(unittest.TestCase):
    def test_parent_first_review_for_science_and_independent_policy(self):
        r = audit_open_prs(graph())
        self.assertEqual(r["total_open_prs"], 4)
        self.assertEqual(r["draft_prs"], 4)
        self.assertEqual(r["family_count"], 2)
        self.assertEqual(r["longest_stack_pr_count"], 3)
        self.assertEqual(r["review_findings"], [])
        reviewed = [p["number"] for p in r["review_order"]]
        self.assertLess(reviewed.index(12), reviewed.index(11))
        self.assertLess(reviewed.index(11), reviewed.index(13))
        n13 = next(p for p in r["review_order"] if p["number"] == 13)
        self.assertEqual(n13["ancestor_chain_including_self"], [12, 11, 13])
        self.assertEqual(n13["parent_pr"], 11)
        self.assertEqual(n13["root_pr"], 12)

    def test_draft_parent_and_ready_child_requires_review_not_merge(self):
        data = graph()
        data[0]["draft"] = False
        r = audit_open_prs(data)
        self.assertEqual(r["non_draft_prs"], 1)
        self.assertEqual(r["review_findings"][0]["kind"], "ready_child_of_draft_parent")

    def test_unknown_base_reported_as_warning_not_assumed_nonexistent(self):
        data = graph()
        data[0]["base"]["ref"] = "unreviewed-existing-branch"
        r = audit_open_prs(data)
        warning = [x for x in r["review_findings"]
                   if x["kind"] == "unrepresented_base_branch"]
        self.assertEqual(len(warning), 1)
        self.assertEqual(warning[0]["number"], 11)

    def test_cycle_of_open_pr_bases_is_rejected(self):
        data = [
            pr(11, "a", "b"),
            pr(12, "b", "c"),
            pr(13, "c", "a"),
        ]
        with self.assertRaisesRegex(ValueError, "Cycle"):
            audit_open_prs(data)

    def test_duplicated_pr_head_is_rejected(self):
        data = graph()
        data[1]["head"]["ref"] = data[2]["head"]["ref"]
        with self.assertRaisesRegex(ValueError, "same source head"):
            audit_open_prs(data)

    def test_duplicated_pr_number_is_rejected(self):
        data = graph()
        data[1]["number"] = data[2]["number"]
        with self.assertRaisesRegex(ValueError, "Duplicate PR number"):
            audit_open_prs(data)

    def test_self_base_invalid(self):
        data = graph()
        data[1]["base"]["ref"] = data[1]["head"]["ref"]
        with self.assertRaisesRegex(ValueError, "own source branch"):
            audit_open_prs(data)

    def test_incomplete_or_closed_pr_data_rejected(self):
        data = graph()
        del data[0]["base"]
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            audit_open_prs(data)
        data = graph()
        data[0]["state"] = "closed"
        with self.assertRaisesRegex(ValueError, "open PR"):
            audit_open_prs(data)

    def test_fork_head_does_not_accidentally_become_same_repo_parent(self):
        data = graph()
        data[2]["head"]["repo"]["full_name"] = "example/forked"
        r = audit_open_prs(data)
        fork = [x for x in r["review_findings"] if x["kind"] == "external_head"]
        self.assertEqual(fork[0]["number"], 12)
        unrepresented = [x for x in r["review_findings"]
                         if x["kind"] == "unrepresented_base_branch"]
        self.assertTrue(any(x["number"] == 11 for x in unrepresented))

    def test_explanatory_markdown_does_not_claim_merge_permission(self):
        rendered = markdown_summary(audit_open_prs(graph()))
        self.assertIn("Parent-before-child review order", rendered)
        self.assertIn("[#12]", rendered)
        self.assertIn("[#13]", rendered)
        self.assertIn("does **not** merge", rendered)
        self.assertIn("**Next steps:**", rendered)

    def test_empty_pr_list_still_produces_non_actionable_report(self):
        report = audit_open_prs([])
        self.assertEqual(report["total_open_prs"], 0)
        self.assertEqual(report["longest_stack_pr_count"], 0)
        self.assertEqual(report["families"], [])
        self.assertIn("No missing-parent", markdown_summary(report))

    def test_out_of_scope_base_repository_fails_closed(self):
        data = graph()
        data[0]["base"]["repo"]["full_name"] = "other/repository"
        with self.assertRaisesRegex(ValueError, "Unexpected repository"):
            audit_open_prs(data)


if __name__ == "__main__":
    unittest.main()
