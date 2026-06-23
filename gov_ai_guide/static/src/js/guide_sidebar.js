/** @odoo-module **/
/**
 * guide_sidebar.js — مكون الشريط الجانبي للمرشد الحكومي
 * مكوّن OWL ثابت يُحمَّل مرة واحدة ولا يُدمَّر طوال جلسة المتصفح
 * يعرض التلميحات بشكل تدريجي مع تمييز المراجع القانونية والتحذيرات
 */

import { Component, useState, useEffect, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { agentState } from "./agent_connector";

/**
 * تحليل نص التلميح واستخراج المراجع القانونية والتحذيرات
 * يُعيد: { html, lawRefs, warnings }
 */
function parseHintText(text) {
    if (!text) return { html: "", lawRefs: [], warnings: [] };

    const lawRefs = [];
    const warnings = [];

    // استخراج أرقام القوانين (مثال: قانون 89/1998، قرار وزاري 250/2019)
    const lawPattern =
        /(?:قانون|لائحة|قرار|معيار|مرسوم)\s+(?:رقم\s+)?(?:وزاري\s+)?[\d٠-٩]+\/[\d٠-٩]+/g;
    let match;
    while ((match = lawPattern.exec(text)) !== null) {
        if (!lawRefs.includes(match[0])) {
            lawRefs.push(match[0]);
        }
    }

    // معالجة النص سطراً سطراً
    const lines = text.split("\n");
    const processedLines = lines.map((line) => {
        let processed = line;

        // تمييز التحذيرات (⚠ أو أسطر تبدأ بـ "تنبيه" أو "⚠")
        if (processed.includes("⚠") || /^تنبيه/i.test(processed.trim())) {
            warnings.push(processed.replace(/^[⚠\s]+/, "").trim());
            processed = `<span class="gov-warning">${escapeHtml(processed)}</span>`;
        } else {
            // تمييز النصوص الغامقة **...**
            processed = escapeHtml(processed).replace(
                /\*\*(.+?)\*\*/g,
                '<strong class="gov-bold">$1</strong>'
            );

            // تمييز أرقام القوانين بشارة ذهبية
            processed = processed.replace(
                /((?:قانون|لائحة|قرار|معيار|مرسوم)\s+(?:رقم\s+)?(?:وزاري\s+)?[\d٠-٩]+\/[\d٠-٩]+)/g,
                '<span class="gov-law-badge">$1</span>'
            );
        }
        return processed;
    });

    const html = processedLines.join("<br/>");
    return { html, lawRefs, warnings };
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

/**
 * الشريط الجانبي الرئيسي — المكوّن الأساسي
 */
export class GovAISidebar extends Component {
    static template = "gov_ai_guide.GovAISidebar";
    static props = {};

    setup() {
        this.agentState = agentState;
        this.connector = useService("gov_ai_agent_connector");

        this.state = useState({
            isExpanded: true,
            followupText: "",
            hintHistory: [],  // آخر 5 تلميحات
            currentParsed: { html: "", lawRefs: [], warnings: [] },
            showHistory: false,
            copySuccess: false,
        });

        // مراقبة تغيير التلميح لتحديث التحليل
        useEffect(
            () => {
                if (agentState.currentHint && !agentState.isStreaming) {
                    const parsed = parseHintText(agentState.currentHint);
                    this.state.currentParsed = parsed;
                    // حفظ في السجل
                    if (agentState.currentHint.trim()) {
                        this._addToHistory({
                            field: agentState.currentField,
                            model: agentState.currentModel,
                            text: agentState.currentHint,
                            timestamp: new Date().toLocaleTimeString("ar-EG"),
                        });
                    }
                } else if (agentState.isStreaming) {
                    // تحديث مستمر أثناء البث
                    this.state.currentParsed = parseHintText(agentState.currentHint);
                }
            },
            () => [agentState.currentHint, agentState.isStreaming]
        );
    }

    /**
     * إضافة تلميح لسجل المحادثة (آخر 5)
     */
    _addToHistory(entry) {
        const history = this.state.hintHistory;
        // تجنب تكرار نفس التلميح
        if (history.length > 0 && history[0].text === entry.text) return;
        history.unshift(entry);
        if (history.length > 5) history.pop();
    }

    /**
     * تبديل حالة الشريط (موسّع / مطوي)
     */
    toggleSidebar() {
        this.state.isExpanded = !this.state.isExpanded;
    }

    /**
     * نسخ نص التلميح للحافظة
     */
    async copyHint() {
        const text = agentState.currentHint;
        if (!text) return;
        try {
            await navigator.clipboard.writeText(text);
            this.state.copySuccess = true;
            setTimeout(() => { this.state.copySuccess = false; }, 2000);
        } catch (e) {
            // fallback لاستخدام execCommand في المتصفحات القديمة
            const ta = document.createElement("textarea");
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            this.state.copySuccess = true;
            setTimeout(() => { this.state.copySuccess = false; }, 2000);
        }
    }

    /**
     * إرسال سؤال متابعة
     */
    async sendFollowup() {
        const question = this.state.followupText.trim();
        if (!question) return;
        this.state.followupText = "";
        await this.connector.sendFollowup(question);
    }

    /**
     * معالجة Enter في حقل السؤال
     */
    onFollowupKeydown(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            this.sendFollowup();
        }
    }

    /**
     * تمييل عرض السجل
     */
    toggleHistory() {
        this.state.showHistory = !this.state.showHistory;
    }

    /**
     * HTML المعالَج للتلميح الحالي كـ markup آمن
     */
    get renderedHint() {
        return markup(this.state.currentParsed.html || "");
    }

    /**
     * HTML معالَج لأي تلميح في السجل
     */
    renderedHistoryHint(text) {
        const { html } = parseHintText(text);
        return markup(html);
    }

    /**
     * الشارة الحكومية — عنوان الشريط
     */
    get headerTitle() {
        return "المرشد الحكومي";
    }

    /**
     * اسم الحقل الحالي بصيغة مقروءة
     */
    get currentFieldDisplay() {
        const field = agentState.currentField;
        if (!field) return "انتظر تركيز أي حقل...";
        return field.replace(/_/g, " ");
    }

    /**
     * هل نعرض مؤشر التحميل؟
     */
    get showLoader() {
        return agentState.isLoading || agentState.isStreaming;
    }

    /**
     * رسالة الحالة لشارة الاتصال
     */
    get connectionStatus() {
        return agentState.isConnected ? "متصل" : "غير متصل";
    }
}

// تسجيل المكوّن كـ systray item ليظهر دائماً في واجهة Odoo
registry.category("systray").add("gov_ai_sidebar", {
    Component: GovAISidebar,
    sequence: 1,  // يظهر في أقصى اليسار من الـ systray (أقصى اليمين في RTL)
});
