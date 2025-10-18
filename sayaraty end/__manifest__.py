# -*- coding: utf-8 -*-
{
    'name': 'Sayaraty',
    'summary': 'إدارة السيارات + تكاليف إضافية + صيانة وتراخيص + مؤشرات وكروت تقارير + تنبيهات',
    'version': '17.0.2.0.0',
    'author': 'Mohamed Magdy',
    'website': 'https://example.com',
    'category': 'Operations/Vehicle',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/vehicle_views.xml',
        'views/report_kpi_views.xml',
        'views/alerts_views.xml',
        'views/menu.xml',
        'data/vehicle_report_kpi_data.xml',
    ],
    'application': True,
}