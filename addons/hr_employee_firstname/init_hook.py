# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

def post_init_hook(env):
    env['hr.employee']._update_employee_names()
