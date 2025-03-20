/** @odoo-module **/
import { _t } from '@web/core/l10n/translation';
import { loadJS } from '@web/core/assets';
import paymentForm from '@payment/js/payment_form';

paymentForm.include({

    tilopayData: undefined,

    /**
     * Prepare the inline form of Tilopay for direct payment.
     *
     * @private
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'tilopay') {
            this._super(...arguments);
            return;
        }

        this.tilopayData ??= {};

        if (flow === 'token') {
            return;
        } else if (this.tilopayData[paymentOptionId]) {
            this._setPaymentFlow('direct');
            loadJS(this.tilopayData[paymentOptionId]['acceptJSUrl']);
            return;
        }

        this._setPaymentFlow('direct');

        const radio = document.querySelector('input[name="o_payment_radio"]:checked');
        const inlineForm = this._getInlineForm(radio);
        const tilopayForm = inlineForm.querySelector('[name="o_tilopay_form"]');
        this.tilopayData[paymentOptionId] = JSON.parse(tilopayForm.dataset['tilopayInlineFormValues']);
        const tilopayJson = this.tilopayData[paymentOptionId];

        let acceptJSUrl = 'https://app.tilopay.com/sdk/v2/sdk_tpay.min.js';
        this.tilopayData[paymentOptionId].acceptJSUrl = acceptJSUrl;

        try {
            await loadJS(acceptJSUrl);
            await this.Tilopay(tilopayJson);
        } catch (error) {
            console.error("Failed to load Tilopay Script:", error);
        }
    },

    /**
     * Trigger the payment processing.
     *
     * @private
     */
    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'tilopay' || flow === 'token') {
            this._super(...arguments);
            return;
        }

        const inputs = Object.values(this._tilopayGetInlineFormInputs(paymentOptionId, paymentMethodCode));
        if (!inputs.every(element => element.reportValidity())) {
            this._enableButton();
            return;
        }

        await this._super(...arguments);
    },

    /**
     * Process the direct payment flow.
     *
     * @private
     */
    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'tilopay') {
            this._super(...arguments);
            return;
        }

        this.TilopayUpdateOptions({
            returnData: JSON.stringify({
                reference: processingValues.reference,
                amount: processingValues.amount,
                currency: processingValues.currency_id,
            })
        });

        try {
            const payment = await this.tiloMakePay();
            this._tilopayHandleResponse(payment, processingValues);
        } catch (error) {
            console.error("Tilopay Payment Error:", error);
            this._displayErrorDialog(_t("Payment Tilopay processing failed"), error.message);
        }
    },

    /**
     * Handle the response from Tilopay.
     *
     * @private
     */
    _tilopayHandleResponse(response, processingValues) {
        if (response.message !== "Success" && response.message !== "") {
            this._displayErrorDialog(_t("Payment Tilopay processing failed"), response.message);
            this._enableButton();
        }
    },

    /**
     * Extract inputs from the Tilopay form.
     *
     * @private
     */
    _tilopayGetInlineFormInputs(paymentOptionId, paymentMethodCode) {
        const form = this.tilopayData[paymentOptionId]['form'];
        return {
            card: form.querySelector('#tlpy_cc_number'),
            expiration: form.querySelector('#tlpy_cc_expiration_date'),
            cvv: form.querySelector('#tlpy_cvv'),
        };
    },

    /**
     * Prepare payment details for Tilopay.
     *
     * @private
     */
    _tilopayGetPaymentDetails(paymentOptionId, paymentMethodCode) {
        const inputs = this._tilopayGetInlineFormInputs(paymentOptionId, paymentMethodCode);
        return {
            cardData: {
                cardNumber: inputs.card.value.replace(/ /g, ''),
                expiration: inputs.expiration.value,
                cardCode: inputs.cvv.value,
            },
        };
    },

    /**
     * Initialize Tilopay with the provided options.
     *
     * @private
     */
    async Tilopay(values) {
        try {
            const initialize = await Tilopay.Init(values);
            await this.tilopayChargeMethods(initialize.methods);
        } catch (error) {
            console.error("Failed to initialize Tilopay:", error);
        }
    },

    /**
     * Populate available payment methods.
     *
     * @private
     */
    async tilopayChargeMethods(methods) {
        const methodSelect = document.getElementById("tlpy_payment_method");
        methods.forEach(method => {
            const option = document.createElement("option");
            option.value = method.id;
            option.text = method.name;
            methodSelect.appendChild(option);
        });
    },

    /**
     * Trigger Tilopay's payment process.
     *
     * @private
     */
    async tiloMakePay() {
        return await Tilopay.startPayment();
    },

    /**
     * Update Tilopay options dynamically.
     *
     * @private
     */
    async TilopayUpdateOptions(values) {
        await Tilopay.updateOptions(values);
    },
});
