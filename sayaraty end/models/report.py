
from odoo import api, fields, models, _

class VehicleReport(models.Model):
    _name = 'vehicle.report'
    _description = 'Vehicle Dashboard KPIs'
    _rec_name = 'name'

    name = fields.Char(default="لوحة تقارير السيارات", readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, readonly=True)

    total_cars = fields.Integer(string="إجمالي العربيات", compute="_compute_kpis", store=False)
    total_purchase = fields.Monetary(string="إجمالي سعر الشراء", compute="_compute_kpis", currency_field='currency_id', store=False)
    sum_extra = fields.Monetary(string="إجمالي التكاليف الإضافية", compute="_compute_kpis", currency_field='currency_id', store=False)
    sum_total_cost = fields.Monetary(string="إجمالي التكلفة النهائية", compute="_compute_kpis", currency_field='currency_id', store=False)
    avg_extra = fields.Monetary(string="متوسط التكلفة الإضافية/عربية", compute="_compute_kpis", currency_field='currency_id', store=False)
    avg_total_cost = fields.Monetary(string="متوسط التكلفة النهائية/عربية", compute="_compute_kpis", currency_field='currency_id', store=False)
    no_price_count = fields.Integer(string="بدون سعر شراء", compute="_compute_kpis", store=False)

    draft_count = fields.Integer(string="مسودة", compute="_compute_kpis", store=False)
    available_count = fields.Integer(string="متاحة", compute="_compute_kpis", store=False)
    sold_count = fields.Integer(string="مباعة", compute="_compute_kpis", store=False)
    archived_count = fields.Integer(string="مؤرشفة", compute="_compute_kpis", store=False)

    @api.depends()
    def _compute_kpis(self):
        Vehicle = self.env['vehicle.vehicle']
        Cost = self.env['vehicle.cost']  # not directly used but kept for extension
        # Counts by state
        state_groups = Vehicle.read_group([], ['__count'], ['state'])
        state_map = {g['state']: g['state_count'] for g in state_groups}
        # Totals
        total_cars = Vehicle.search_count([])
        total_purchase = Vehicle.read_group([('price','!=',False)], ['price:sum'], [])[0]['price_sum'] if Vehicle else 0.0
        sums = Vehicle.read_group([], ['extra_total:sum', 'total_cost:sum'], [])
        no_price_count = Vehicle.search_count([('price','=',False)])
        sum_extra = sums[0].get('extra_total_sum') or 0.0
        sum_total_cost = sums[0].get('total_cost_sum') or 0.0
        avg_extra = (sum_extra / total_cars) if total_cars else 0.0
        avg_total_cost = (sum_total_cost / total_cars) if total_cars else 0.0

        for rec in self:
            rec.total_cars = total_cars
            rec.total_purchase = total_purchase or 0.0
            rec.sum_extra = sum_extra
            rec.sum_total_cost = sum_total_cost
            rec.avg_extra = avg_extra
            rec.avg_total_cost = avg_total_cost
            rec.no_price_count = no_price_count
            rec.draft_count = state_map.get('draft', 0)
            rec.available_count = state_map.get('available', 0)
            rec.sold_count = state_map.get('sold', 0)
            rec.archived_count = state_map.get('archived', 0)
