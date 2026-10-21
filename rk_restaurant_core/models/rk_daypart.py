# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RkDaypart(models.Model):
    """A trading day-part. Labour, sales and prep all get reported by this dimension."""

    _name = "rk.daypart"
    _description = "Day-part"
    _order = "sequence, hour_from"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    hour_from = fields.Float(string="From (hour)", required=True, help="24h decimal, e.g. 18.5 = 18:30.")
    hour_to = fields.Float(string="To (hour)", required=True, help="If lower than 'From', the day-part wraps midnight.")
    overnight = fields.Boolean(compute="_compute_overnight", store=True)
    config_ids = fields.Many2many("pos.config", "rk_daypart_pos_config_rel", "daypart_id", "config_id", string="Outlets")
    color = fields.Integer(default=0)

    _daypart_code_uniq = models.Constraint("UNIQUE(code)", "The day-part code must be unique.")

    @api.depends("hour_from", "hour_to")
    def _compute_overnight(self):
        for daypart in self:
            daypart.overnight = daypart.hour_to <= daypart.hour_from

    @api.constrains("hour_from", "hour_to")
    def _check_hours(self):
        for daypart in self:
            if not (0 <= daypart.hour_from <= 24 and 0 <= daypart.hour_to <= 24):
                raise ValidationError(_("Day-part hours must be between 0 and 24."))
            if daypart.hour_from == daypart.hour_to:
                raise ValidationError(_("A day-part must have a non-zero length."))

    def _contains_hour(self, hour):
        """True when ``hour`` (0–24 decimal) falls inside this day-part."""
        self.ensure_one()
        if self.overnight:
            return hour >= self.hour_from or hour < self.hour_to
        return self.hour_from <= hour < self.hour_to

    @api.model
    def _find_for_hour(self, hour, config=None):
        """Return the most specific day-part covering ``hour`` for ``config``."""
        domain = [("active", "=", True)]
        dayparts = self.search(domain)
        if config:
            specific = dayparts.filtered(lambda d: config in d.config_ids)
            dayparts = specific or dayparts
        for daypart in dayparts.sorted(lambda d: (len(d.config_ids) and 0 or 1, -d.sequence, -d.hour_from)):
            if daypart._contains_hour(hour):
                return daypart
        return self.browse()

    @api.depends("name", "hour_from", "hour_to")
    def _compute_display_name(self):
        for daypart in self:
            daypart.display_name = f"{daypart.name} ({int(daypart.hour_from):02d}:00–{int(daypart.hour_to):02d}:00)"
