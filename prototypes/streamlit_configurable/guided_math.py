"""Pure, validated edits from guided UI widgets to the *same* typed JSON IR.

No eval, no second solver model, and no background mutation of mathematical
terms. When an edit is inconsistent, the entire original model is preserved.
"""
from __future__ import annotations

from copy import deepcopy

from qopt.core.math_ir import validate_ir


def _get(items: list[dict], name: str, key: str) -> dict:
    for item in items:
        if item[key] == name:
            return item
    raise ValueError(f"Unknown {key}: {name}")


def apply_guided_edit(source: dict, parameters: dict, operation: str, **edit) -> dict:
    """Apply one atomic semantic change and validate the COMPLETE resulting IR.

    All edits re-use validate_ir, also used for the preview/SCIP compilation.
    Never silently drop terms or constraints when deleting a variable/row.
    """
    validate_ir(source, parameters)
    data = deepcopy(source)
    variables = data["variables"]
    objective = data["objective"]
    rows = data["constraints"]
    names = [v["name"] for v in variables]
    if operation == "variable_update":
        variable = _get(variables, edit["name"], "name")
        variable.update(domain=edit["domain"], lower=edit["lower"], upper=edit["upper"])
    elif operation == "variable_add":
        if edit["name"] in names:
            raise ValueError("Duplicate variable identifiers")
        variables.append({
            "name": edit["name"], "domain": edit["domain"],
            "lower": edit["lower"], "upper": edit["upper"],
        })
    elif operation == "variable_remove":
        name = edit["name"]
        _get(variables, name, "name")
        if (name in objective["linear"] or
            any(name in (t["first"], t["second"]) for t in objective["quadratic"]) or
            any(name in r["linear"] for r in rows)):
            raise ValueError(
                "Variable is referenced: clear objective, quadratic and row terms before deleting"
            )
        variables[:] = [v for v in variables if v["name"] != name]
    elif operation == "objective_update":
        objective["sense"] = edit["sense"]
        objective["constant"] = edit["constant"]
    elif operation in ("linear_set", "linear_remove"):
        if edit["name"] not in names:
            raise ValueError("Unknown objective variable")
        if operation == "linear_set":
            objective["linear"][edit["name"]] = edit["coefficient"]
        else:
            objective["linear"].pop(edit["name"], None)
    elif operation in ("quadratic_set", "quadratic_remove"):
        a, b = edit["first"], edit["second"]
        if a == b or a not in names or b not in names:
            raise ValueError("Quadratic pair requires two distinct existing variables")
        matches = [
            t for t in objective["quadratic"]
            if {t["first"], t["second"]} == {a, b}
        ]
        if operation == "quadratic_set":
            if matches:
                matches[0]["coefficient"] = edit["coefficient"]
            else:
                objective["quadratic"].append({
                    "first": a, "second": b, "coefficient": edit["coefficient"]
                })
        else:
            if not matches:
                raise ValueError("No such quadratic pair to remove")
            objective["quadratic"].remove(matches[0])
    elif operation == "constraint_add":
        name = edit["name"]
        if any(r["id"] == name for r in rows):
            raise ValueError("Duplicate linear constraint ID")
        rows.append({"id": name, "sense": edit["sense"], "rhs": edit["rhs"], "linear": {}})
    elif operation == "constraint_update":
        row = _get(rows, edit["name"], "id")
        if edit["name"] in parameters.get("rhs_overrides", {}):
            raise ValueError("An RHS override is active for this row; remove or edit the override first")
        row["sense"] = edit["sense"]
        row["rhs"] = edit["rhs"]
    elif operation in ("constraint_coefficient", "constraint_coefficient_remove"):
        row = _get(rows, edit["name"], "id")
        if edit["variable"] not in names:
            raise ValueError("Unknown constraint variable")
        if operation == "constraint_coefficient":
            row["linear"][edit["variable"]] = edit["coefficient"]
        else:
            row["linear"].pop(edit["variable"], None)
    elif operation == "constraint_remove":
        name = edit["name"]
        _get(rows, name, "id")
        if name in parameters.get("rhs_overrides", {}):
            raise ValueError("Remove the named RHS parameter override before deleting this row")
        rows[:] = [r for r in rows if r["id"] != name]
    else:
        raise ValueError(f"Unsupported guided edit: {operation}")
    validate_ir(data, parameters)
    return data


def parse_components(vars_text: str, objective_text: str, rows_text: str) -> dict:
    import json

    return {
        "classification": "SYNTHETIC_TYPED_OPTIMIZATION",
        "variables": json.loads(vars_text),
        "objective": json.loads(objective_text),
        "constraints": json.loads(rows_text),
    }
