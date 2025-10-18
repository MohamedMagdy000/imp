
from odoo import api, fields, models, _

class SayaratyVehicle(models.Model):
    _name = "vehicle.vehicle"
    _description = "Vehicle"
    _order = "create_date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic info
    name = fields.Char(string="اسم العربية", required=True, tracking=True)
    vin = fields.Char(string="رقم الشاسيه (VIN)", tracking=True)
    plate_no = fields.Char(string="رقم اللوحات", tracking=True)
    model_year = fields.Char(string="الموديل/سنة الصنع")
    color = fields.Char(string="اللون")

    # Status
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('available', 'متاحة'),
        ('sold', 'مباعة'),
        ('archived', 'مؤرشفة'),
    ], string="الحالة", default='draft', tracking=True)

    # Pricing
    price = fields.Monetary(string="سعر الشراء", currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='العملة', default=lambda self: self.env.company.currency_id.id)

    # Extra costs
    cost_line_ids = fields.One2many('vehicle.cost', 'vehicle_id', string="تكاليف إضافية")
    extra_total = fields.Monetary(string="إجمالي التكاليف الإضافية", compute="_compute_totals", store=True, currency_field='currency_id')
    total_cost = fields.Monetary(string="إجمالي تكلفة العربية", compute="_compute_totals", store=True, currency_field='currency_id')

    # License / maintenance
    license_number = fields.Char(string="رقم الرخصة")
    license_expiry_date = fields.Date(string="تاريخ انتهاء الرخصة")
    insurance_expiry_date = fields.Date(string="تاريخ انتهاء التأمين")
    inspection_expiry_date = fields.Date(string="تاريخ انتهاء الفحص")

    odometer_km = fields.Integer(string="عداد (كم)")
    last_oil_change_km = fields.Integer(string="آخر تغيير زيت عند (كم)")
    last_oil_change_date = fields.Date(string="تاريخ آخر تغيير زيت")
    oil_change_interval_km = fields.Integer(string="فاصل تغيير الزيت (كم)", default=10000)
    next_oil_change_km = fields.Integer(string="التغيير القادم عند (كم)", compute="_compute_next_oil_km", store=True)

    license_expires_soon = fields.Boolean(string="الرخصة ستنتهي قريبًا", compute="_compute_alerts", store=True)
    needs_oil_change = fields.Boolean(string="يحتاج تغيير زيت", compute="_compute_alerts", store=True)

    @api.depends('price', 'cost_line_ids.amount')
    def _compute_totals(self):
        for rec in self:
            extra = sum(rec.cost_line_ids.mapped('amount'))
            rec.extra_total = extra
            rec.total_cost = (rec.price or 0.0) + extra

    @api.depends('last_oil_change_km', 'oil_change_interval_km')
    def _compute_next_oil_km(self):
        for rec in self:
            base_km = rec.last_oil_change_km or 0
            interval = rec.oil_change_interval_km or 0
            rec.next_oil_change_km = base_km + interval if interval else 0

    @api.depends('license_expiry_date', 'odometer_km', 'next_oil_change_km')
    def _compute_alerts(self):
        from datetime import timedelta
        today = fields.Date.context_today(self)
        soon_limit = today + timedelta(days=7)
        for rec in self:
            rec.license_expires_soon = bool(rec.license_expiry_date and today <= rec.license_expiry_date <= soon_limit)
            rec.needs_oil_change = bool(rec.next_oil_change_km and rec.odometer_km and rec.odometer_km >= rec.next_oil_change_km)

    # State actions
    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_set_available(self):
        self.write({'state': 'available'})

    def action_set_sold(self):
        self.write({'state': 'sold'})

    def action_set_archived(self):
        self.write({'state': 'archived'})


class VehicleCost(models.Model):
    _name = "vehicle.cost"
    _description = "Vehicle Additional Cost"
    _order = "date desc, id desc"

    vehicle_id = fields.Many2one('vehicle.vehicle', string="العربية", required=True, ondelete='cascade')
    date = fields.Date(string="التاريخ", default=fields.Date.context_today, required=True)
    cost_type = fields.Selection([
        ('maintenance', 'صيانة'),
        ('renewal', 'تجديد'),
        ('fuel', 'وقود'),
        ('fees', 'رسوم/ترخيص'),
        ('parts', 'قطع غيار'),
        ('transport', 'نقل'),
        ('shipping', 'شحن'),
        ('insurance', 'تأمين'),
        ('inspection', 'فحص/كشف'),
        ('wash', 'غسيل/نظافة'),
        ('taxes', 'ضرائب/دمغات'),
        ('other', 'أخرى'),
    ], string="نوع التكلفة", required=True)
    description = fields.Char(string="الوصف")
    vendor_bill = fields.Char(string="فاتورة مورد")
    amount = fields.Monetary(string="المبلغ", required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='العملة', default=lambda self: self.env.company.currency_id.id)
