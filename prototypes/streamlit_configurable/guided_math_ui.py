"""Optional Streamlit guided controls for synthetic, bounded typed mathematical IR.

Raw JSON component editors remain the single source of truth. Buttons update
those existing widget values in an on_click callback (BEFORE Streamlit rerun),
never construct a second model or change the solver definition.
"""
from __future__ import annotations

import json
from hashlib import sha256

import streamlit as st

from guided_math import apply_guided_edit, parse_components
from qopt.core.math_ir import validate_ir


def _commit(preset: str, operation: str, **change) -> None:
    keys = (
        "typed-vars-" + preset,
        "typed-objective-" + preset,
        "typed-constraints-" + preset,
    )
    flag = "guided-status-" + preset
    try:
        data = parse_components(*(st.session_state[key] for key in keys))
        parameters = json.loads(st.session_state["parameters-" + preset])
        updated = apply_guided_edit(data, parameters, operation, **change)
        # Values are updated in callback before rerun; no modification to
        # already instantiated widgets or shadow copies of the mathematical IR.
        for key, section in zip(keys, ("variables", "objective", "constraints")):
            st.session_state[key] = json.dumps(updated[section], indent=2)
        st.session_state.pop("preview_fingerprint", None)
        st.session_state.pop("completed_run", None)
        st.session_state[flag] = ("success", "Change validated. Review the new formulation.")
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        st.session_state[flag] = ("error", f"Change rejected; original math unchanged: {exc}")


def _button(label: str, preset: str, action: str, **values) -> None:
    st.button(
        label, on_click=_commit, args=(preset, action),
        kwargs=values, key=f"guided-btn-{preset}-{action}",
    )


def show_guided_controls(preset: str, variables_text: str,
                         objective_text: str, constraints_text: str,
                         parameters_text: str) -> None:
    # Advanced JSON fields and guided widgets are ONE model. Reset only
    # guided display state when the authoritative JSON changes, before any
    # guided widgets are instantiated in this rerun. This avoids a stale
    # coefficient or relation being shown after direct advanced edits.
    signature = sha256(json.dumps([
        variables_text, objective_text, constraints_text, parameters_text,
    ], separators=(",", ":")).encode("utf-8")).hexdigest()
    identity = "guided-source-signature-" + preset
    if st.session_state.get(identity) != signature:
        for key in list(st.session_state.keys()):
            if key.startswith("guide-") and ("-" + preset) in key:
                del st.session_state[key]
        st.session_state[identity] = signature

    with st.expander("Guided math controls — no JSON editing required", expanded=True):
        st.caption(
            "Changes update the SAME source as the advanced JSON fields above. "
            "Invalid changes are rejected atomically. Model preview and results "
            "must be regenerated after a successful edit."
        )
        status = st.session_state.get("guided-status-" + preset)
        if status:
            (st.success if status[0] == "success" else st.error)(status[1])
        try:
            model = parse_components(variables_text, objective_text, constraints_text)
            parameters = json.loads(parameters_text)
            ir = validate_ir(model, parameters)
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            st.warning(f"Guided editor needs a valid typed source first: {exc}")
            return
        variables = ir["variables"]
        names = [v["name"] for v in variables]
        var_map = {v["name"]: v for v in variables}
        rows = ir["constraints"]
        row_map = {r["id"]: r for r in rows}
        objective = ir["objective"]

        var_tab, objective_tab, row_tab = st.tabs(
            ["Variables and bounds", "Objective and interactions", "Constraints"]
        )
        with var_tab:
            selected = st.selectbox("Select variable to edit", names,
                                    key="guide-var-" + preset)
            item = var_map[selected]
            domain = st.selectbox(
                "Variable domain", ["binary", "integer", "continuous"],
                index=["binary", "integer", "continuous"].index(item["domain"]),
                key=f"guide-domain-{preset}-{selected}",
            )
            if domain == "binary":
                st.caption("Binary variables always have exact bounds [0,1].")
                low, high = 0., 1.
            else:
                low = st.number_input(
                    "Variable lower bound", value=float(item["lower"]),
                    key=f"guide-low-{preset}-{selected}", step=1.,
                )
                high = st.number_input(
                    "Variable upper bound", value=float(item["upper"]),
                    key=f"guide-high-{preset}-{selected}", step=1.,
                )
            _button("Apply variable domain and bounds", preset, "variable_update",
                    name=selected, domain=domain, lower=low, upper=high)
            st.divider()
            new_name = st.text_input("New variable ID", value="new_variable",
                                     key="guide-add-var-name-" + preset)
            new_domain = st.selectbox("New variable domain",
                                      ["binary", "integer", "continuous"],
                                      key="guide-add-var-domain-" + preset)
            _button("Add variable", preset, "variable_add",
                    name=new_name, domain=new_domain,
                    lower=0, upper=1)
            st.caption("New integer/continuous variables start at [0,1]; edit their bounds above.")
            _button("Remove selected variable", preset, "variable_remove", name=selected)
            st.caption("To remove a referenced variable, clear its objective and row terms first.")

        with objective_tab:
            sense = st.selectbox(
                "Optimization direction", ["minimize", "maximize"],
                index=["minimize", "maximize"].index(objective["sense"]),
                key="guide-sense-" + preset,
            )
            constant = st.number_input(
                "Objective constant", value=float(objective["constant"]),
                key="guide-constant-" + preset,
            )
            _button("Apply objective direction and constant", preset,
                    "objective_update", sense=sense, constant=constant)
            target = st.selectbox("Objective variable", names,
                                  key="guide-obj-var-" + preset)
            coefficient = st.number_input(
                "Linear objective coefficient",
                value=float(objective["linear"].get(target, 0.)),
                key=f"guide-linear-{preset}-{target}",
            )
            _button("Set linear coefficient", preset, "linear_set",
                    name=target, coefficient=coefficient)
            _button("Remove linear coefficient term", preset, "linear_remove",
                    name=target)
            binary_vars = [v["name"] for v in variables if v["domain"] == "binary"]
            if len(binary_vars) >= 2:
                a = st.selectbox("First interacting binary variable", binary_vars,
                                 key="guide-pair-a-" + preset)
                b_candidates = [x for x in binary_vars if x != a]
                b = st.selectbox("Second interacting binary variable", b_candidates,
                                 key=f"guide-pair-b-{preset}-{a}")
                prior = next((
                    t["coefficient"] for t in objective["quadratic"]
                    if {t["first"], t["second"]} == {a, b}
                ), 0.)
                strength = st.number_input(
                    "Binary interaction coefficient", value=float(prior),
                    key=f"guide-quadratic-{preset}-{min(a,b)}-{max(a,b)}",
                )
                _button("Set binary interaction", preset, "quadratic_set",
                        first=a, second=b, coefficient=strength)
                _button("Remove binary interaction", preset, "quadratic_remove",
                        first=a, second=b)
            else:
                st.caption("Two binary variables are required for a quadratic interaction.")

        with row_tab:
            if rows:
                rid = st.selectbox("Select constraint row", list(row_map),
                                   key="guide-row-" + preset)
                row = row_map[rid]
                relation = st.selectbox(
                    "Constraint relation", ["<=", "==", ">="],
                    index=["<=", "==", ">="].index(row["sense"]),
                    key=f"guide-relation-{preset}-{rid}",
                )
                rhs = st.number_input(
                    "Constraint right-hand side", value=float(row["rhs"]),
                    key=f"guide-rhs-{preset}-{rid}",
                )
                if rid in parameters.get("rhs_overrides", {}):
                    st.warning(
                        "A named RHS override is active: remove or edit it in the parameter "
                        "field before changing this row's base RHS."
                    )
                _button("Apply constraint relation and RHS", preset, "constraint_update",
                        name=rid, sense=relation, rhs=rhs)
                rv = st.selectbox("Constraint variable", names,
                                  key=f"guide-row-var-{preset}-{rid}")
                cv = st.number_input(
                    "Constraint variable coefficient",
                    value=float(row["linear"].get(rv, 0.)),
                    key=f"guide-row-coeff-{preset}-{rid}-{rv}",
                )
                _button("Set constraint coefficient", preset, "constraint_coefficient",
                        name=rid, variable=rv, coefficient=cv)
                _button("Remove constraint coefficient term", preset,
                        "constraint_coefficient_remove", name=rid, variable=rv)
                _button("Remove selected constraint", preset, "constraint_remove", name=rid)
            else:
                st.info("No linear constraints: direct QUBO may be eligible if all variables are binary.")
            st.divider()
            new_row = st.text_input(
                "New constraint ID", value="new_limit",
                key="guide-new-row-" + preset,
            )
            new_relation = st.selectbox(
                "New constraint relation", ["<=", "==", ">="],
                key="guide-new-relation-" + preset,
            )
            new_rhs = st.number_input(
                "New constraint right-hand side", value=1.,
                key="guide-new-rhs-" + preset,
            )
            _button("Add constraint", preset, "constraint_add",
                    name=new_row, sense=new_relation, rhs=new_rhs)
            st.caption(
                "A new row starts with zero coefficients. Choose its variables above. "
                "Named RHS overrides in Advanced Parameters take precedence."
            )
