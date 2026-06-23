/** @odoo-module **/

import { Component, useState, useEffect, markup, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { agentState } from "./agent_connector";

// ─── helper functions ────────────────────────────────────────────────────────

function escapeHtml(t) {
    if (!t) return "";
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function parseHintText(text) {
    if (!text) return { html: "", lawRefs: [] };
    const lawRefs = [];
    const pat = /(?:قانون|لائحة|قرار|معيار|مرسوم)\s+(?:رقم\s+)?(?:وزاري\s+)?[\d٠-٩]+\/[\d٠-٩]+/g;
    let m;
    while ((m = pat.exec(text)) !== null) {
        if (!lawRefs.includes(m[0])) lawRefs.push(m[0]);
    }
    const html = text.split("\n").map((line) => {
        if (line.includes("⚠") || /^تنبيه/i.test(line.trim()))
            return `<span style="color:#e53935">${escapeHtml(line)}</span>`;
        return escapeHtml(line)
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(
                /((?:قانون|لائحة|قرار|معيار|مرسوم)\s+(?:رقم\s+)?(?:وزاري\s+)?[\d٠-٩]+\/[\d٠-٩]+)/g,
                '<span style="background:#c8a84b;color:#1a2744;padding:1px 5px;border-radius:3px;font-size:11px">$1</span>'
            );
    }).join("<br/>");
    return { html, lawRefs };
}

// ─── الشريط الجانبي — يُعرض مباشرة على document.body ────────────────────────
// هذا المكوّن لا يُستخدم كـ OWL component؛ يُعالَج يدوياً في DOM

function buildSidebarDOM() {
    const sidebar = document.createElement("div");
    sidebar.id = "gov-ai-sidebar-container";
    sidebar.dir = "rtl";
    sidebar.style.cssText = [
        "position:fixed", "top:0", "right:0", "height:100vh",
        "width:320px", "background:#1a2744", "z-index:99999",
        "display:flex", "flex-direction:column",
        "font-family:Cairo,Arial,sans-serif", "color:#f0f4ff",
        "border-left:1px solid #243460", "border-top:3px solid #c8a84b",
        "box-shadow:-4px 0 20px rgba(0,0,0,.4)", "overflow:hidden",
        "transition:width .25s ease",
    ].join(";");
    document.body.appendChild(sidebar);
    return sidebar;
}

function renderSidebar(container, state) {
    const { expanded, parsed, copyOk, followupText } = state;

    if (!expanded) {
        container.style.width = "48px";
        container.innerHTML = `
            <div id="gov-collapsed-btn" style="
                display:flex;align-items:center;justify-content:center;
                height:100%;cursor:pointer;font-size:22px;color:#c8a84b;
                writing-mode:vertical-rl;
            " title="المرشد الحكومي">&#x1F3DB;</div>`;
        return;
    }

    container.style.width = "320px";
    const loaderHtml = (agentState.isLoading || agentState.isStreaming) ? `
        <div style="padding:12px;text-align:center;color:#9bacc8;font-size:13px">
            جارٍ تحليل الحقل...
        </div>` : "";
    const hintHtml = agentState.currentHint ? `
        ${parsed.lawRefs.map(r => `<span style="background:#c8a84b;color:#1a2744;
            padding:2px 7px;border-radius:3px;font-size:11px;margin:2px;
            display:inline-block">${escapeHtml(r)}</span>`).join("")}
        <div style="padding:10px;font-size:13px;line-height:1.7">${parsed.html}</div>
        <div style="padding:0 10px 8px">
            <button id="gov-copy-btn" style="
                background:transparent;border:1px solid #c8a84b;color:#c8a84b;
                padding:4px 12px;border-radius:3px;cursor:pointer;font-size:12px;
                font-family:inherit
            ">${copyOk ? "✓ تم النسخ" : "نسخ النص"}</button>
        </div>` : `
        <div style="padding:20px;text-align:center;color:#9bacc8;font-size:13px;line-height:1.8">
            انقر على أي حقل في النموذج لتلقي الإرشاد الحكومي المناسب
        </div>`;
    const followupHtml = agentState.currentHint && !agentState.isLoading ? `
        <div style="padding:8px;border-top:1px solid #243460;display:flex;gap:6px">
            <input id="gov-followup-inp" type="text" value="${escapeHtml(followupText)}"
                placeholder="سؤال متابعة..." dir="rtl"
                style="flex:1;background:#243460;border:1px solid #355080;color:#f0f4ff;
                    padding:6px 8px;border-radius:3px;font-family:inherit;font-size:12px"/>
            <button id="gov-followup-btn" style="
                background:#c8a84b;color:#1a2744;border:none;padding:6px 10px;
                border-radius:3px;cursor:pointer;font-family:inherit;font-size:12px
            ">إرسال</button>
        </div>` : "";
    const connDot = agentState.isConnected
        ? `<span style="width:7px;height:7px;border-radius:50%;background:#43a047;display:inline-block;margin-right:4px"></span>`
        : `<span style="width:7px;height:7px;border-radius:50%;background:#e53935;display:inline-block;margin-right:4px"></span>`;
    const fieldName = (agentState.currentField || "انتظر تركيز أي حقل...").replace(/_/g, " ");

    container.innerHTML = `
        <!-- header -->
        <div style="display:flex;align-items:center;gap:8px;padding:10px 12px;
            background:#1a2744;border-bottom:1px solid #243460;flex-shrink:0;min-height:52px">
            <svg viewBox="0 0 40 40" width="32" height="32" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0">
                <circle cx="20" cy="20" r="18" fill="#c8a84b" stroke="#1a2744" stroke-width="2"/>
                <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle"
                    font-size="16" fill="#1a2744" font-weight="bold">م</text>
            </svg>
            <div style="flex:1;display:flex;align-items:center;gap:4px">
                ${connDot}
                <span style="font-size:13px;font-weight:700;color:#c8a84b">المرشد الحكومي</span>
            </div>
            <button id="gov-toggle-btn" style="
                background:transparent;border:none;color:#c8a84b;cursor:pointer;
                font-size:16px;padding:4px 8px
            ">&#x25C4;</button>
        </div>
        <!-- field info -->
        <div style="padding:6px 12px;background:#243460;font-size:11px;color:#9bacc8;flex-shrink:0">
            الحقل: <span style="color:#f0f4ff">${escapeHtml(fieldName)}</span>
        </div>
        <!-- hint area -->
        <div style="flex:1;overflow-y:auto;padding:4px">
            ${loaderHtml || hintHtml}
        </div>
        ${followupHtml}
        <!-- footer -->
        <div style="padding:6px 12px;border-top:1px solid #243460;font-size:10px;
            color:#9bacc8;text-align:center;flex-shrink:0">
            المرشد الحكومي الذكي
        </div>
    `;
}

// ─── Systray icon — المكوّن الوحيد المسجَّل في systray (أيقونة بسيطة فقط) ──

export class GovAITrayIcon extends Component {
    static template = "gov_ai_guide.GovAITrayIcon";
    static props = {};

    setup() {
        this._container = null;
        this._state = { expanded: true, parsed: { html: "", lawRefs: [] }, copyOk: false, followupText: "" };
        this._connector = null;
        this._interval = null;

        onMounted(() => {
            // بناء الـ sidebar على document.body
            this._container = buildSidebarDOM();
            this._rerender();

            // مراقبة agentState بـ polling خفيف
            this._interval = setInterval(() => this._rerender(), 300);

            // try get connector
            try {
                this._connector = this.__owl__?.app?.env?.services?.gov_ai_agent_connector || null;
            } catch (_e) {}

            // event delegation على الـ container
            this._container.addEventListener("click", (e) => this._onClick(e));
            this._container.addEventListener("input", (e) => {
                if (e.target.id === "gov-followup-inp") {
                    this._state.followupText = e.target.value;
                }
            });
            this._container.addEventListener("keydown", (e) => {
                if (e.target.id === "gov-followup-inp" && e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    this._sendFollowup();
                }
            });
        });

        onWillUnmount(() => {
            clearInterval(this._interval);
            if (this._container) this._container.remove();
        });
    }

    _rerender() {
        if (!this._container) return;
        try {
            renderSidebar(this._container, this._state);
        } catch (_e) {}
    }

    _onClick(e) {
        const id = e.target.closest("[id]")?.id;
        if (id === "gov-toggle-btn" || id === "gov-collapsed-btn") {
            this._state.expanded = !this._state.expanded;
            this._rerender();
        } else if (id === "gov-copy-btn") {
            const text = agentState.currentHint;
            if (!text) return;
            navigator.clipboard?.writeText(text).catch(() => {
                const ta = document.createElement("textarea");
                ta.value = text;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand("copy");
                document.body.removeChild(ta);
            });
            this._state.copyOk = true;
            this._rerender();
            setTimeout(() => { this._state.copyOk = false; this._rerender(); }, 2000);
        } else if (id === "gov-followup-btn") {
            this._sendFollowup();
        }
    }

    async _sendFollowup() {
        const q = this._state.followupText.trim();
        if (!q) return;
        this._state.followupText = "";
        if (this._connector) {
            try { await this._connector.sendFollowup(q); } catch (_e) {}
        }
    }
}

// القالب البسيط للأيقونة في الـ systray — لا يحتوي position:fixed
registry.category("systray").add("gov_ai_sidebar", {
    Component: GovAITrayIcon,
    sequence: 1,
});
