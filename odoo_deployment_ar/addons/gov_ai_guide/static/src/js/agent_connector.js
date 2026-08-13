/** @odoo-module **/
/**
 * agent_connector.js — مدير اتصال المرشد الحكومي
 * خدمة Singleton تدير الاتصال مع الخادم وتبث الردود للشريط الجانبي
 * تستخدم Server-Sent Events (SSE) للبث الحقيقي token-by-token
 * مع fallback لـ REST API عند الحاجة
 */

import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";
import { session } from "@web/session";

// مفتاح الجلسة في localStorage — يُشترك بين جميع التبويبات
const SESSION_TOKEN_KEY = "gov_ai_session_token";
// فترات إعادة المحاولة بالتضاعف الأسي (بالمللي ثانية)
const RETRY_DELAYS = [1000, 2000, 4000, 8000];
// الفاصل الزمني لنبضة الحياة (30 ثانية)
const PING_INTERVAL = 30000;

/**
 * إنشاء أو استرجاع رمز الجلسة الفريد لهذا المتصفح
 * يضمن استمرارية الجلسة عبر تحديثات الصفحة
 */
function getOrCreateSessionToken() {
    let token = localStorage.getItem(SESSION_TOKEN_KEY);
    if (!token) {
        token = crypto.randomUUID ? crypto.randomUUID() : generateUUID();
        localStorage.setItem(SESSION_TOKEN_KEY, token);
    }
    return token;
}

function generateUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

/**
 * الحالة التفاعلية المشتركة — يقرأها guide_sidebar.js مباشرة
 * reactive() يضمن تحديث الواجهة تلقائياً عند أي تغيير
 */
export const agentState = reactive({
    sessionToken: getOrCreateSessionToken(),
    isConnected: false,
    isLoading: false,
    currentHint: "",
    currentField: "",
    currentModel: "",
    isStreaming: false,
    lastError: null,
    messageQueue: [], // رسائل مؤجلة أثناء انقطاع الاتصال
    sessionId: null,
    totalHints: 0,
});

class AgentConnectorService {
    constructor(env, services) {
        this.env = env;
        this.rpc = services.rpc;
        this.notification = services.notification;

        this._eventSource = null;  // SSE connection
        this._pingTimer = null;
        this._retryCount = 0;
        this._currentStreamController = null;

        // بدء الاتصال فور تهيئة الخدمة
        this._initialize();
    }

    /**
     * تهيئة الخدمة: تسجيل الجلسة على الخادم وبدء نبضة الحياة
     */
    async _initialize() {
        try {
            const result = await this.rpc("/gov_ai/ws/connect", {
                session_token: agentState.sessionToken,
            });
            if (result && result.status === "connected") {
                agentState.isConnected = true;
                agentState.sessionId = result.session_id;
                this._retryCount = 0;
                this._startPing();
                // إرسال الرسائل المؤجلة
                this._flushQueue();
            }
        } catch (e) {
            console.warn("[GovAI] فشل الاتصال الأولي:", e);
            agentState.isConnected = false;
            this._scheduleReconnect();
        }
    }

    /**
     * نبضة الحياة — تُبقي الجلسة حية على الخادم
     */
    _startPing() {
        this._pingTimer = setInterval(async () => {
            try {
                await this.rpc("/gov_ai/session/ping", {
                    session_token: agentState.sessionToken,
                });
            } catch (e) {
                // إذا فشلت النبضة، نحاول إعادة الاتصال
                agentState.isConnected = false;
                this._scheduleReconnect();
            }
        }, PING_INTERVAL);
    }

    /**
     * جدولة إعادة الاتصال بالتضاعف الأسي
     */
    _scheduleReconnect() {
        const delay = RETRY_DELAYS[Math.min(this._retryCount, RETRY_DELAYS.length - 1)];
        this._retryCount++;
        setTimeout(() => this._initialize(), delay);
    }

    /**
     * إرسال طلب تلميح — النقطة الرئيسية التي يستدعيها field_tracker
     * يستخدم SSE للبث الحقيقي، مع fallback لـ REST
     */
    async sendHintRequest(payload) {
        // إلغاء أي بث جارٍ
        if (this._currentStreamController) {
            this._currentStreamController.abort();
            this._currentStreamController = null;
        }

        agentState.currentField = payload.field || "";
        agentState.currentModel = payload.model || "";
        agentState.currentHint = "";
        agentState.isLoading = true;
        agentState.isStreaming = false;
        agentState.lastError = null;

        if (!agentState.isConnected) {
            // احفظ في الطابور وأعِد الاتصال
            agentState.messageQueue.push(payload);
            this._scheduleReconnect();
            return;
        }

        // بناء URL للبث SSE
        const params = new URLSearchParams({
            session_token: agentState.sessionToken,
            model: payload.model || "",
            field: payload.field || "",
            value: String(payload.value || "").substring(0, 200),
            view_type: payload.view_type || "form",
        });
        const streamUrl = `/gov_ai/stream?${params.toString()}`;

        const controller = new AbortController();
        this._currentStreamController = controller;

        try {
            const response = await fetch(streamUrl, {
                signal: controller.signal,
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            agentState.isStreaming = true;
            agentState.isLoading = false;

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                if (controller.signal.aborted) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop(); // الأخير قد يكون غير مكتمل

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this._handleStreamEvent(data);
                        } catch (e) {
                            // تجاهل الأسطر غير الصالحة
                        }
                    }
                }
            }
        } catch (e) {
            if (e.name !== "AbortError") {
                console.warn("[GovAI] فشل البث، محاولة REST:", e);
                await this._fallbackToRest(payload);
            }
        } finally {
            agentState.isStreaming = false;
            agentState.isLoading = false;
            this._currentStreamController = null;
        }
    }

    /**
     * معالجة أحداث SSE الواردة
     */
    _handleStreamEvent(data) {
        switch (data.type) {
            case "hint_chunk":
                agentState.currentHint += data.text || "";
                break;
            case "hint_done":
                agentState.isStreaming = false;
                agentState.isLoading = false;
                agentState.totalHints++;
                break;
            case "hint_error":
                agentState.lastError = data.message || "خطأ غير محدد";
                agentState.isLoading = false;
                agentState.isStreaming = false;
                break;
        }
    }

    /**
     * Fallback لـ REST API عند فشل SSE
     */
    async _fallbackToRest(payload) {
        try {
            agentState.isLoading = true;
            const result = await this.rpc("/gov_ai/hint", {
                session_token: agentState.sessionToken,
                ...payload,
            });
            if (result && result.text) {
                agentState.currentHint = result.text;
                agentState.totalHints++;
            }
        } catch (e) {
            agentState.lastError = "تعذّر الاتصال بالمرشد الحكومي";
            agentState.currentHint = this._getOfflineFallback(payload);
        } finally {
            agentState.isLoading = false;
        }
    }

    /**
     * تلميح محلي عند انعدام الاتصال تماماً
     */
    _getOfflineFallback(payload) {
        return (
            "**الإجراء المطلوب:**\n" +
            "تعذّر الاتصال بالمرشد الحكومي. يُرجى التحقق من اتصالك بالشبكة.\n\n" +
            "**تنبيهات هامة:**\n" +
            "⚠ تأكد من صحة البيانات المُدخلة وفق اللوائح الحكومية المعمول بها.\n\n" +
            "**الخطوة التالية:**\n" +
            "راجع دليل الإجراءات المعتمد بجهتك."
        );
    }

    /**
     * إرسال سؤال متابعة من الشريط الجانبي
     */
    async sendFollowup(question) {
        agentState.isLoading = true;
        try {
            const result = await this.rpc("/gov_ai/followup", {
                session_token: agentState.sessionToken,
                question,
            });
            if (result && result.text) {
                agentState.currentHint = result.text;
            }
        } catch (e) {
            agentState.lastError = "فشل إرسال السؤال";
        } finally {
            agentState.isLoading = false;
        }
    }

    /**
     * إرسال الرسائل المؤجلة بعد إعادة الاتصال
     */
    async _flushQueue() {
        while (agentState.messageQueue.length > 0) {
            const payload = agentState.messageQueue.shift();
            await this.sendHintRequest(payload);
        }
    }

    destroy() {
        if (this._pingTimer) clearInterval(this._pingTimer);
        if (this._currentStreamController) this._currentStreamController.abort();
    }
}

// تسجيل الخدمة في Odoo's service registry
export const agentConnectorService = {
    name: "gov_ai_agent_connector",
    dependencies: ["rpc", "notification"],
    start(env, services) {
        return new AgentConnectorService(env, services);
    },
};

registry.category("services").add("gov_ai_agent_connector", agentConnectorService);
