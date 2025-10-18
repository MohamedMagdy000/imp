
from odoo import api, fields, models, _

class VehicleReportKPI(models.Model):
    _name = 'vehicle.report.kpi'
    _description = 'Vehicle Report KPIs (one record per card)'
    _rec_name = 'name'

    code = fields.Selection([
        ('total_cars', 'إجمالي العربيات'),
        ('total_purchase', 'إجمالي سعر الشراء'),
        ('sum_extra', 'إجمالي التكاليف الإضافية'),
        ('sum_total_cost', 'إجمالي التكلفة النهائية'),
        ('avg_total_cost', 'متوسط التكلفة النهائية/عربية'),
        ('avg_extra', 'متوسط التكلفة الإضافية/عربية'),
        ('no_price', 'بدون سعر شراء'),
        ('draft_count', 'مسودة'),
        ('available_count', 'متاحة'),
        ('sold_count', 'مباعة'),
        ('archived_count', 'مؤرشفة'),
        ('license_due', 'رخصة بتنتهي قريبًا'),
        ('oil_due', 'يحتاج تغيير زيت'),
    ], required=True, index=True)
    name = fields.Char(required=True)
    color_hex = fields.Char(string='لون الخلفية', default='#BBDEFB')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    value = fields.Monetary(string='القيمة', compute='_compute_value', currency_field='currency_id', store=False)
    value_int = fields.Integer(string='قيمة عددية', compute='_compute_value_int', store=False)

    @api.depends()
    def _compute_value(self):
        Vehicle = self.env['vehicle.vehicle']
        total_cars = Vehicle.search_count([])
        total_purchase = Vehicle.read_group([('price','!=',False)], ['price:sum'], [])[0]['price_sum'] if Vehicle else 0.0
        sums = Vehicle.read_group([], ['extra_total:sum', 'total_cost:sum'], [])
        sum_extra = sums[0].get('extra_total_sum') or 0.0
        sum_total_cost = sums[0].get('total_cost_sum') or 0.0
        avg_total_cost = (sum_total_cost / total_cars) if total_cars else 0.0
        avg_extra = (sum_extra / total_cars) if total_cars else 0.0
        for rec in self:
            rec.value = 0.0
            if rec.code == 'total_purchase':
                rec.value = total_purchase or 0.0
            elif rec.code == 'sum_extra':
                rec.value = sum_extra
            elif rec.code == 'sum_total_cost':
                rec.value = sum_total_cost
            elif rec.code == 'avg_total_cost':
                rec.value = avg_total_cost
            elif rec.code == 'avg_extra':
                rec.value = avg_extra
            else:
                rec.value = 0.0

    @api.depends()
    def _compute_value_int(self):
        Vehicle = self.env['vehicle.vehicle']
        total_cars = Vehicle.search_count([])
        no_price = Vehicle.search_count([('price','=',False)])
        state_groups = Vehicle.read_group([], ['__count'], ['state'])
        smap = {g['state']: g['state_count'] for g in state_groups}
        license_due_count = Vehicle.search_count([('license_expires_soon','=',True)])
        oil_due_count = Vehicle.search_count([('needs_oil_change','=',True)])
        for rec in self:
            rec.value_int = 0
            if rec.code == 'total_cars':
                rec.value_int = total_cars
            elif rec.code == 'no_price':
                rec.value_int = no_price
            elif rec.code == 'draft_count':
                rec.value_int = smap.get('draft', 0)
            elif rec.code == 'available_count':
                rec.value_int = smap.get('available', 0)
            elif rec.code == 'sold_count':
                rec.value_int = smap.get('sold', 0)
            elif rec.code == 'archived_count':
                rec.value_int = smap.get('archived', 0)
            elif rec.code == 'license_due':
                rec.value_int = license_due_count
            elif rec.code == 'oil_due':
                rec.value_int = oil_due_count


license_due_html = fields.Html(string='قائمة الرخص', compute='_compute_alert_lists', sanitize=True)
oil_due_html = fields.Html(string='قائمة الزيت', compute='_compute_alert_lists', sanitize=True)

def _format_vehicle_row(self, v, kind='license'):
    if kind == 'license':
        date = v.license_expiry_date or ''
        extra = f" — ينتهي: {date}" if date else ''
    else:
        nxt = v.next_oil_change_km or 0
        odo = v.odometer_km or 0
        extra = f" — عداد: {odo} / التالي: {nxt} كم"
    plate = v.plate_no or '-'
    name = v.name or str(v.id)
    return f"<li><strong>{name}</strong> <span style='opacity:.7'>(لوحات: {plate})</span>{extra}</li>"

def _compute_alert_lists(self):
    Vehicle = self.env['vehicle.vehicle']
    license_due = Vehicle.search([('license_expires_soon','=',True)], limit=5, order='license_expiry_date asc, name')
    oil_due = Vehicle.search([('needs_oil_change','=',True)], limit=5, order='next_oil_change_km asc, name')
    lic_html = "<ul style='margin:8px 0 0 16px; padding:0 0 0 8px;'>%s</ul>" % "".join(self._format_vehicle_row(v, 'license') for v in license_due) if license_due else "<div style='opacity:.6; margin-top:6px;'>لا توجد عربيات مطلوبة حاليًا</div>"
    oil_html = "<ul style='margin:8px 0 0 16px; padding:0 0 0 8px;'>%s</ul>" % "".join(self._format_vehicle_row(v, 'oil') for v in oil_due) if oil_due else "<div style='opacity:.6; margin-top:6px;'>لا توجد عربيات مطلوبة حاليًا</div>"
    for rec in self:
        rec.license_due_html = lic_html
        rec.oil_due_html = oil_html
