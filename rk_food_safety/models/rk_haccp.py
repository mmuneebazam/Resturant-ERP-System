# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RkHaccpChecklist(models.Model):
    """A reusable set of checkpoints, e.g. 'Opening — cold chain'."""

    _name = "rk.haccp.checklist"
    _description = "HACCP checklist"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    frequency = fields.Selection(
        [("per_shift", "Every shift"), ("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
        default="daily", required=True,
    )
    outlet_ids = fields.Many2many("rk.outlet", "rk_haccp_checklist_outlet_rel", "checklist_id", "outlet_id", string="Outlets")
    line_ids = fields.One2many("rk.haccp.checklist.line", "checklist_id", string="Checkpoints", copy=True)
    instructions = fields.Text()

    _checklist_code_uniq = models.Constraint("UNIQUE(code)", "The checklist code must be unique.")


class RkHaccpChecklistLine(models.Model):
    _name = "rk.haccp.checklist.line"
    _description = "Checklist checkpoint"
    _order = "checklist_id, sequence, id"

    checklist_id = fields.Many2one("rk.haccp.checklist", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Checkpoint", required=True)
    is_temperature = fields.Boolean(string="Temperature check", default=False)
    temp_min = fields.Float(string="Min °C")
    temp_max = fields.Float(string="Max °C")
    requires_photo = fields.Boolean()
    instruction = fields.Char()


class RkHaccpCheck(models.Model):
    """One completed (or attempted) checklist at one outlet."""

    _name = "rk.haccp.check"
    _description = "HACCP check"
    _order = "date desc, id desc"
    _inherit = ["mail.thread"]

    name = fields.Char(default=lambda self: _("New"), readonly=True, copy=False)
    checklist_id = fields.Many2one("rk.haccp.checklist", required=True, ondelete="restrict")
    outlet_id = fields.Many2one("rk.outlet", required=True, ondelete="restrict", index=True)
    company_id = fields.Many2one(related="outlet_id.company_id", store=True)
    date = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    user_id = fields.Many2one("res.users", string="Checked by", default=lambda self: self.env.user)
    line_ids = fields.One2many("rk.haccp.check.line", "check_id", string="Results", copy=True)
    state = fields.Selection(
        [("draft", "Draft"), ("pass", "Passed"), ("fail", "Failed")], default="draft", required=True, tracking=True
    )
    failure_count = fields.Integer(compute="_compute_failure_count", store=True)
    corrective_action = fields.Text()
    verified_by_id = fields.Many2one("res.users", string="Verified by")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rk.haccp.check") or _("New")
        return super().create(vals_list)

    @api.depends("line_ids.is_ok", "line_ids.is_temperature")
    def _compute_failure_count(self):
        for check in self:
            check.failure_count = len(check.line_ids.filtered(lambda l: l.is_temperature and not l.is_ok))

    @api.onchange("checklist_id")
    def _onchange_checklist_id(self):
        if not self.checklist_id:
            return
        self.line_ids = [
            (5, 0, 0),
            *[(0, 0, {
                "sequence": line.sequence,
                "name": line.name,
                "is_temperature": line.is_temperature,
                "temp_min": line.temp_min,
                "temp_max": line.temp_max,
                "instruction": line.instruction,
            }) for line in self.checklist_id.line_ids],
        ]

    def action_load_checkpoints(self):
        """Copy the checklist's checkpoints into the check (also used by seeding)."""
        for check in self:
            check.line_ids.unlink()
            check.line_ids = [
                (0, 0, {
                    "sequence": line.sequence,
                    "name": line.name,
                    "is_temperature": line.is_temperature,
                    "temp_min": line.temp_min,
                    "temp_max": line.temp_max,
                    "instruction": line.instruction,
                }) for line in check.checklist_id.line_ids
            ]
        return True

    def action_validate(self):
        for check in self:
            if not check.line_ids:
                raise UserError(_("There is nothing to validate: load the checkpoints first."))
            check._compute_failure_count()
            if check.failure_count and not check.corrective_action:
                raise UserError(
                    _("A failing temperature needs a corrective action before the check can be validated.")
                )
            check.state = "fail" if check.failure_count else "pass"
            check.message_post(
                body=_("Check %(state)s: %(failures)s failing checkpoint(s).",
                       state=check.state, failures=check.failure_count)
            )
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class RkHaccpCheckLine(models.Model):
    _name = "rk.haccp.check.line"
    _description = "HACCP check line"
    _order = "check_id, sequence, id"

    check_id = fields.Many2one("rk.haccp.check", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Checkpoint", required=True)
    is_temperature = fields.Boolean(string="Temperature check")
    temp_min = fields.Float(string="Min °C")
    temp_max = fields.Float(string="Max °C")
    temp_value = fields.Float(string="Reading °C")
    is_ok = fields.Boolean(compute="_compute_is_ok", store=True, string="OK")
    instruction = fields.Char()
    note = fields.Char()

    @api.depends("temp_value", "temp_min", "temp_max", "is_temperature")
    def _compute_is_ok(self):
        for line in self:
            if not line.is_temperature:
                line.is_ok = True
            elif line.temp_min or line.temp_max:
                line.is_ok = line.temp_min <= line.temp_value <= line.temp_max
            else:
                line.is_ok = True
