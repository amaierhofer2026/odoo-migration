/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// Odoo 18 rewrite of the former Odoo 11 portal script. The legacy DOM-ready helper and
// frontend jQuery were both removed in Odoo 18, so this is reimplemented as a public
// widget. It only starts on the subscription close modal (#wc-modal-close, rendered only
// when display_close is true), which replaces the old page-guard check. Behaviour is
// preserved 1:1: on click the Confirm button is disabled, a spinner is prepended and the
// surrounding form is submitted (forced, since the disabled attribute would otherwise
// cancel the native submit).
publicWidget.registry.ItkContractSubmit = publicWidget.Widget.extend({
    selector: '#wc-modal-close',
    events: {
        'click .contract-submit': '_onContractSubmit',
    },

    _onContractSubmit(ev) {
        const button = ev.currentTarget;
        button.setAttribute('disabled', 'disabled');
        button.insertAdjacentHTML('afterbegin', '<i class="fa fa-refresh fa-spin"></i> ');
        const form = button.closest('form');
        if (form) {
            form.submit();
        }
    },
});

export default publicWidget.registry.ItkContractSubmit;
