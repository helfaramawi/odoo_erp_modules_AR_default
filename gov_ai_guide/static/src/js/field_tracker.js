/** @odoo-module **/
/**
 * field_tracker.js — خدمة تتبع الحقل النشط
 * تراقب نشاط المستخدم في النماذج وترسل طلبات التلميح عند تغيير الحقل
 * تدعم: النماذج العادية، معالجات الخطوات، تبويبات Notebook، شريط الحالة، سطور One2many
 */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { agentState } from "./agent_connector";

// وقت الانتظار قبل إرسال الطلب (بعد توقف المستخدم عن الكتابة)
const DEBOUNCE_MS = 800;

// آخر حقل تم إرسال تلميح له — لتجنب الإرسال المتكرر لنفس الحقل
let _lastSentKey = "";
let _debounceTimer = null;

/**
 * بناء مفتاح فريد للحقل لاكتشاف التغييرات
 */
function buildFieldKey(model, field, value) {
    return `${model}|${field}|${String(value || "").substring(0, 50)}`;
}

/**
 * إرسال طلب التلميح مع debounce
 * يتجاهل الطلبات المتكررة لنفس الحقل/القيمة
 */
function requestHint(connector, payload) {
    const key = buildFieldKey(payload.model, payload.field, payload.value);
    if (key === _lastSentKey) return; // نفس الحقل والقيمة — لا نرسل مجدداً

    clearTimeout(_debounceTimer);
    _debounceTimer = setTimeout(() => {
        _lastSentKey = key;
        connector.sendHintRequest(payload);
    }, DEBOUNCE_MS);
}

/**
 * استخراج اسم النموذج من المتحكم أو العنصر DOM
 */
function extractModel(formController) {
    try {
        return (
            formController?.model?.config?.resModel ||
            formController?.props?.resModel ||
            ""
        );
    } catch {
        return "";
    }
}

/**
 * استخراج معرّف السجل الحالي
 */
function extractRecordId(formController) {
    try {
        return formController?.model?.root?.resId || null;
    } catch {
        return null;
    }
}

/**
 * استخراج قيمة حقل من سجل Odoo
 */
function extractFieldValue(record, fieldName) {
    if (!record || !fieldName) return "";
    try {
        const val = record.data?.[fieldName];
        if (val === null || val === undefined) return "";
        if (typeof val === "object") {
            // Many2one يُعيد [id, name]
            return val.display_name || val[1] || String(val.id || "");
        }
        return String(val);
    } catch {
        return "";
    }
}

/**
 * خدمة تتبع الحقل — تُهيَّأ مرة واحدة عند تحميل التطبيق
 */
class FieldTrackerService {
    constructor(env, services) {
        this.env = env;
        this.connector = services.gov_ai_agent_connector;
        this._setupGlobalListeners();
    }

    /**
     * إعداد مستمعي الأحداث العالميين على مستوى الـ document
     * نستخدم event delegation بدلاً من إضافة مستمع لكل حقل
     */
    _setupGlobalListeners() {
        // تتبع focus على حقول الإدخال
        document.addEventListener("focusin", (e) => this._onFocusIn(e), true);

        // تتبع تغييرات القيم في الحقول الخاصة (select, checkbox)
        document.addEventListener("change", (e) => this._onChange(e), true);
    }

    /**
     * معالج حدث التركيز — يُطلق عند دخول المستخدم لأي حقل
     */
    _onFocusIn(event) {
        const target = event.target;
        if (!this._isFormField(target)) return;

        const payload = this._buildPayload(target);
        if (payload) {
            requestHint(this.connector, payload);
        }
    }

    /**
     * معالج حدث التغيير — للحقول التي لا تحتوي text (select, checkbox, Many2one)
     */
    _onChange(event) {
        const target = event.target;
        if (!this._isFormField(target)) return;

        const payload = this._buildPayload(target);
        if (payload) {
            requestHint(this.connector, payload);
        }
    }

    /**
     * هل العنصر حقل إدخال في نموذج Odoo؟
     */
    _isFormField(element) {
        if (!element) return false;
        const tag = element.tagName?.toLowerCase();
        const isInput = ["input", "select", "textarea"].includes(tag);
        if (!isInput) return false;

        // تجاهل حقول البحث والفلاتر
        const type = element.type?.toLowerCase();
        if (type === "search" || type === "hidden") return false;

        // تأكد من أن العنصر داخل نموذج Odoo
        return !!element.closest(".o_form_view, .o_form_sheet");
    }

    /**
     * بناء payload من العنصر المُركَّز
     * يستخرج: model، field_name، value، view_type، record_id
     */
    _buildPayload(element) {
        try {
            // اسم الحقل من data attributes أو name
            const fieldName =
                element.closest("[name]")?.getAttribute("name") ||
                element.getAttribute("name") ||
                element.getAttribute("id") ||
                "";

            if (!fieldName || fieldName.startsWith("__")) return null;

            // اسم النموذج من أقرب عنصر view
            const formEl = element.closest(".o_form_view");
            const model = formEl?.dataset?.model || agentState.currentModel || "";

            // القيمة الحالية
            let value = element.value || "";
            // لـ Many2one نقرأ النص من span مجاور
            if (!value) {
                const displayEl = element.closest(".o_field_widget")?.querySelector(
                    ".o_form_uri, .o_tag_badge_text, span[class*='display']"
                );
                if (displayEl) value = displayEl.textContent?.trim() || "";
            }

            // نوع العرض
            const viewType = formEl ? "form" : "list";

            // معرّف السجل
            const recordId = formEl?.dataset?.activeId
                ? parseInt(formEl.dataset.activeId)
                : null;

            // تحقق من أن الحقل في وضع التحرير
            const isReadonly = element.readOnly || element.disabled ||
                element.closest(".o_field_widget")?.classList.contains("o_readonly");
            if (isReadonly) return null;

            return {
                model,
                field: fieldName,
                value,
                view_type: viewType,
                record_id: recordId,
                form_state: "edit",
            };
        } catch (e) {
            return null;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Patch على FormController لتتبع تغييرات الخطوات والتبويبات وشريط الحالة
// ─────────────────────────────────────────────────────────────────────────────

patch(FormController.prototype, {
    setup() {
        super.setup();
        // نحاول الوصول للـ connector عبر service registry
        try {
            this._govAiConnector = useService("gov_ai_agent_connector");
        } catch {
            this._govAiConnector = null;
        }
    },

    /**
     * مراقبة تغيير حقل الحالة (status bar) في workflow
     */
    async saveRecord() {
        const result = await super.saveRecord(...arguments);
        if (this._govAiConnector && this.model?.root) {
            const model = extractModel(this);
            const statusField = this._getStatusField();
            if (statusField) {
                const value = extractFieldValue(this.model.root, statusField);
                requestHint(this._govAiConnector, {
                    model,
                    field: statusField,
                    value,
                    view_type: "form",
                    record_id: extractRecordId(this),
                });
            }
        }
        return result;
    },

    /**
     * الحصول على اسم حقل الحالة من تعريف العرض
     */
    _getStatusField() {
        try {
            const statusBarEl = document.querySelector(".o_statusbar_status");
            if (!statusBarEl) return null;
            const activeBtn = statusBarEl.querySelector(
                "button.btn-primary, button[aria-checked='true']"
            );
            return activeBtn?.dataset?.field || null;
        } catch {
            return null;
        }
    },
});

// ─────────────────────────────────────────────────────────────────────────────
// تتبع تغيير صفحة Notebook
// ─────────────────────────────────────────────────────────────────────────────

// نستمع لنقرات تبويبات Notebook عبر event delegation
document.addEventListener("click", (e) => {
    const notebookTab = e.target.closest(".o_notebook .nav-link");
    if (!notebookTab) return;

    const pageTitle = notebookTab.textContent?.trim() || "";
    const formEl = notebookTab.closest(".o_form_view");
    const model = formEl?.dataset?.model || agentState.currentModel || "";

    if (model && pageTitle) {
        // نُخبر الـ connector بتغيير التبويب
        agentState.currentHint = "";
        agentState.currentField = `notebook_tab: ${pageTitle}`;
    }
});

// تسجيل الخدمة
export const fieldTrackerService = {
    name: "gov_ai_field_tracker",
    dependencies: ["gov_ai_agent_connector"],
    start(env, services) {
        return new FieldTrackerService(env, services);
    },
};

registry.category("services").add("gov_ai_field_tracker", fieldTrackerService);
