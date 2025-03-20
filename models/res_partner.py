# -*- coding: utf-8 -*-
#################################################################################
# Author      : ABL Solutions.
# Copyright(c): 2017-Present ABL Solutions.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################

from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    first_name = fields.Char('First Name', help="First Name of Customer/Supplier")
    last_name = fields.Char('Last Name', help="Last Name of Customer/Supplier")
    surname = fields.Char('Surname', help="Surname of Customer/Supplier")

    @api.model_create_multi
    def create(self, vals_list):
        """ Override create method to set 'name' based on 'first_name', 'last_name', and 'surname'. """
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '*':
                # Prepare name field from first_name, last_name, and surname
                vals['name'] = self._generate_full_name(vals)
        return super(ResPartner, self).create(vals_list)

    def write(self, values):
        """ Override write method to update 'name' if first_name, last_name, or surname is modified. """
        if 'first_name' in values or 'last_name' in values or 'surname' in values:
            if not values.get('name') or values['name'] == '*':
                for record in self:
                    updated_values = {**record.read(['first_name', 'last_name', 'surname'])[0], **values}
                    values['name'] = self._generate_full_name(updated_values)
        return super(ResPartner, self).write(values)
    
    def _generate_full_name(self, vals):
        """Generate the full name from first_name, last_name, and surname."""
        first_name = vals.get('first_name', '') or ''
        last_name = vals.get('last_name', '') or ''
        surname = vals.get('surname', '') or ''
        
        # Concatenate names while avoiding extra spaces
        name = ' '.join(part for part in [first_name, last_name, surname] if part).strip()
        return name or '*'
