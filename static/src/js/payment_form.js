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

        console.log("Tilopay Initialization Started");

        this.tilopayData ??= {}; // Initialize if not already done.

        if (flow === 'token') return;

        if (this.tilopayData[paymentOptionId]) {
            this._setPaymentFlow('direct');
            await loadJS(this.tilopayData[paymentOptionId].acceptJSUrl);
            return;
        }

        this._setPaymentFlow('direct');

        const radio = document.querySelector('input[name="o_payment_radio"]:checked');
        const inlineForm = this._getInlineForm(radio);

        if (!inlineForm) {
            console.error("Tilopay: Payment option form not found.");
            return;
        }

        const tilopayForm = inlineForm.querySelector('[name="o_tilopay_form"]');

        if (!tilopayForm) {
            console.error("Tilopay form not found. Check your template rendering.");
            return;
        }

        try {
            this.tilopayData[paymentOptionId] = JSON.parse(tilopayForm.dataset['tilopayInlineFormValues']);
            this.tilopayData[paymentOptionId].form = tilopayForm;
            this.tilopayData[paymentOptionId].acceptJSUrl = 'https://app.tilopay.com/sdk/v2/sdk_tpay.min.js';

            console.log("Tilopay Form Data Loaded Successfully:", this.tilopayData[paymentOptionId]);

            await loadJS(this.tilopayData[paymentOptionId].acceptJSUrl);
            await this.Tilopay(this.tilopayData[paymentOptionId]);
            console.log("Tilopay Initialized Successfully.");
        } catch (error) {
            console.error("Error during Tilopay Initialization:", error);
        }
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

        try {
            this.TilopayUpdateOptions({
                returnData: JSON.stringify({
                    reference: processingValues.reference,
                    amount: processingValues.amount,
                    currency: processingValues.currency_id,
                })
            });

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
        if (!response || response.message !== "Success") {
            const errorMsg = response?.message || _t("Unknown error occurred.");
            console.error("Tilopay Error:", errorMsg);
            this._displayErrorDialog(_t("Payment Tilopay processing failed"), errorMsg);
            this._enableButton();
            return;
        }
        console.log("Tilopay Payment Processed Successfully.");
    },

    /**
     * Extract inputs from the Tilopay form.
     *
     * @private
     */
    _tilopayGetInlineFormInputs(paymentOptionId) {
        const form = this.tilopayData[paymentOptionId]?.form;
        if (!form) {
            console.error("Tilopay form not initialized.");
            return {};
        }
        
        return {
            card: form.querySelector('#tlpy_cc_number'),
            expiration: form.querySelector('#tlpy_cc_expiration_date'),
            cvv: form.querySelector('#tlpy_cvv'),
        };
    },

    /**
     * Initialize Tilopay with the provided options.
     *
     * @private
     */
    async Tilopay(values) {
        try {
            if (typeof Tilopay === 'undefined') {
                console.error("Tilopay SDK is not loaded.");
                return;
            }
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
        if (!methodSelect) return;

        methodSelect.innerHTML = ''; // Clear previous options.
        
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
        if (typeof Tilopay === 'undefined') {
            console.error("Tilopay SDK is not available.");
            return;
        }
        return await Tilopay.startPayment();
    },

    /**
     * Update Tilopay options dynamically.
     *
     * @private
     */
    async TilopayUpdateOptions(values) {
        try {
            if (typeof Tilopay === 'undefined') {
                console.error("Tilopay SDK is not loaded.");
                return;
            }
            await Tilopay.updateOptions(values);
        } catch (error) {
            console.error("Error updating Tilopay options:", error);
        }
    },
});
