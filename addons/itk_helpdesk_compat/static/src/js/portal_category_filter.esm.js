/** @odoo-module **/

import { registry } from "@web/core/registry";
import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * ITK Helpdesk Portal — 2-step Category/Subcategory Selection
 *
 * When the user picks a main category, the subcategory dropdown
 * is filtered to show only subcategories belonging to that parent.
 */
publicWidget.registry.itkHelpdeskCategoryFilter = publicWidget.Widget.extend({
    selector: "#sub_category_id",
    events: {
        "change #category_id": "_onCategoryChange",
    },

    start() {
        this._super(...arguments);
        this._allOptions = [...this.el.querySelectorAll("option")];
        // Store parent info from data attributes
        this._subcatMap = {};
        for (const opt of this._allOptions) {
            const parentId = opt.getAttribute("data-parent");
            if (parentId) {
                this._subcatMap[opt.value] = parseInt(parentId);
            }
        }
    },

    _onCategoryChange(ev) {
        const categoryId = parseInt(ev.target.value);
        const subcatGroup = document.getElementById("subcategory_group");
        const subcatSelect = this.el;

        // Reset selection
        subcatSelect.value = "";

        if (!categoryId) {
            subcatGroup.style.display = "none";
            return;
        }
        subcatGroup.style.display = "";

        // Show/hide options based on parent
        let hasVisible = false;
        for (const opt of this._allOptions) {
            if (!opt.value) continue; // skip empty option
            const parentId = this._subcatMap[opt.value];
            if (parentId === categoryId) {
                opt.style.display = "";
                hasVisible = true;
            } else {
                opt.style.display = "none";
            }
        }

        // Hide group if no matching subcategories
        if (!hasVisible) {
            subcatGroup.style.display = "none";
        }
    },
});

registry.category("public_widgets").add(
    "itk_helpdesk_category_filter",
    publicWidget.registry.itkHelpdeskCategoryFilter,
);
