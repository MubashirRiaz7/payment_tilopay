# -*- coding: utf-8 -*-
#################################################################################
# Author      : ABL Solutions.
# Copyright(c): 2017-Present ABL Solutions.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################

import json
import logging
import ast

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

PAYMENT_STATUS_MAPPING = {
    '1': 'Processed',
    'done': ('Processed', 'Completed'),
    'cancel': ('Voided', 'Expired'),
}

class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override to find the transaction based on Tilopay data."""
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'tilopay' or len(tx) == 1:
            return tx
        
        # Parsing the returnData for reference lookup
        try:
            return_data = ast.literal_eval(notification_data.get('returnData', '{}'))
            reference = return_data.get('reference')
            if not reference:
                raise ValidationError(_("Tilopay: Missing reference in return data."))
        except Exception as e:
            raise ValidationError(_("Tilopay: Invalid return data format - %s") % str(e))

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'tilopay')])
        if not tx:
            raise ValidationError(_("Tilopay: No transaction found matching reference %s.") % reference)
        
        return tx

    def _process_notification_data(self, notification_data):
        """Override to process the transaction based on Tilopay data."""
        super()._process_notification_data(notification_data)
        if self.provider_code != 'tilopay':
            return

        if not notification_data:
            self._set_canceled(_("The customer left the payment page."))
            return

        # Parsing the notification data
        try:
            return_data = ast.literal_eval(notification_data.get('returnData', '{}'))
        except Exception as e:
            _logger.error("Tilopay: Error parsing returnData - %s", str(e))
            self._set_error(_("Tilopay: Invalid returnData format received."))
            return

        # Validating required fields
        amount = return_data.get('amount')
        currency_code = return_data.get('currency')
        if not amount or not currency_code:
            self._set_error(_("Tilopay: Missing amount or currency information."))
            return

        try:
            currency = self.env['res.currency'].browse(int(currency_code))
        except Exception:
            self._set_error(_("Tilopay: Invalid currency code received."))
            return

        # Comparing amounts and currencies
        if self.currency_id.compare_amounts(float(amount), self.amount) != 0:
            self._set_error(_("Tilopay: Mismatching transaction amounts."))
            return

        if currency.name != self.currency_id.name:
            self._set_error(_("Tilopay: Mismatching currency codes."))
            return

        # Updating provider reference
        txn_id = notification_data.get('tilopay-transaction')
        if not txn_id:
            self._set_error(_("Tilopay: Missing transaction ID."))
            return

        self.provider_reference = txn_id

        # Processing payment status
        payment_status = notification_data.get('code')
        _logger.info('----- Tilopay Notification Data ------')
        _logger.info(str(notification_data))

        if payment_status == '1':
            self._set_done()
        elif payment_status != '1':
            state_message = notification_data.get('description', "No error description provided.")
            self._set_canceled(state_message=state_message)
        else:
            _logger.error("Tilopay: Invalid payment status received (%s) for transaction reference %s.", 
                          payment_status, self.reference)
            self._set_error(_("Tilopay: Invalid payment status received - %s") % payment_status)
