/** @odoo-module **/

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

// ─── DOM Sidebar (pure JS, no OWL) ──────────────────────────────────────────

class GovSidebar {
    constructor(connector) {
        this._connector = connector;
        this._expanded = true;
        this._copyOk = false;
        this._followup = "";
        this._parsed = { html: "", lawRefs: [] };
        this._el = null;
        this._intervalId = null;
    }

    mount() {
        this._el = document.createElement("div");
        this._el.id = "gov-ai-sidebar-root";
        // نحسب ارتفاع الـ navbar لنبدأ الشريط من تحته
        const navbar = document.querySelector(".o_main_navbar");
        const navH = navbar ? navbar.offsetHeight : 46;
        Object.assign(this._el.style, {
            position: "fixed", top: navH + "px", left: "0",
            height: `calc(100vh - ${navH}px)`, width: "320px",
            background: "#1a2744", zIndex: "10000",
            display: "flex", flexDirection: "column",
            fontFamily: "Cairo,Arial,sans-serif", color: "#f0f4ff",
            borderLeft: "1px solid #243460", borderTop: "3px solid #c8a84b",
            boxShadow: "-4px 0 20px rgba(0,0,0,.4)", overflow: "hidden",
            direction: "rtl", transition: "width .25s ease",
        });
        document.body.appendChild(this._el);

        this._el.addEventListener("click", (e) => this._handleClick(e));
        this._el.addEventListener("input", (e) => {
            if (e.target.dataset.role === "followup") {
                this._followup = e.target.value;
            }
        });
        this._el.addEventListener("keydown", (e) => {
            if (e.target.dataset.role === "followup" && e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this._sendFollowup();
            }
        });

        this._render();
        this._intervalId = setInterval(() => this._render(), 400);
    }

    _render() {
        if (!this._el) return;
        try {
            if (agentState.currentHint && !agentState.isStreaming) {
                this._parsed = parseHintText(agentState.currentHint);
            }
            this._el.style.width = this._expanded ? "320px" : "48px";
            this._el.innerHTML = this._expanded ? this._expandedHTML() : this._collapsedHTML();
        } catch (_e) {}
    }

    _collapsedHTML() {
        return `<div data-action="toggle" style="
            height:100%;display:flex;align-items:center;justify-content:center;
            cursor:pointer;color:#c8a84b;font-size:20px;writing-mode:vertical-rl;
            user-select:none" title="المرشد الحكومي">م</div>`;
    }

    _expandedHTML() {
        const field = (agentState.currentField || "انتظر تركيز أي حقل...").replace(/_/g, " ");
        const dot = agentState.isConnected
            ? `<span style="width:7px;height:7px;border-radius:50%;background:#43a047;display:inline-block;margin-left:4px;flex-shrink:0"></span>`
            : `<span style="width:7px;height:7px;border-radius:50%;background:#e53935;display:inline-block;margin-left:4px;flex-shrink:0"></span>`;

        let hintArea = "";
        if (agentState.isLoading || agentState.isStreaming) {
            hintArea = `<div style="padding:16px;text-align:center;color:#9bacc8;font-size:13px">جارٍ تحليل الحقل...</div>`;
        } else if (agentState.lastError) {
            hintArea = `<div style="padding:12px;color:#e53935;font-size:13px">${escapeHtml(agentState.lastError)}</div>`;
        } else if (agentState.currentHint) {
            const refs = this._parsed.lawRefs.map(r =>
                `<span style="background:#c8a84b;color:#1a2744;padding:2px 7px;border-radius:3px;font-size:11px;margin:2px;display:inline-block">${escapeHtml(r)}</span>`
            ).join("");
            hintArea = `
                ${refs ? `<div style="padding:8px 10px 4px">${refs}</div>` : ""}
                <div style="padding:8px 12px;font-size:13px;line-height:1.8">${this._parsed.html}</div>
                <div style="padding:0 12px 8px">
                    <button data-action="copy" style="
                        background:transparent;border:1px solid #c8a84b;color:#c8a84b;
                        padding:4px 14px;border-radius:3px;cursor:pointer;
                        font-size:12px;font-family:inherit">
                        ${this._copyOk ? "✓ تم النسخ" : "نسخ النص"}
                    </button>
                </div>`;
        } else {
            hintArea = `<div style="padding:24px 16px;text-align:center;color:#9bacc8;font-size:13px;line-height:1.9">
                انقر على أي حقل في النموذج لتلقي الإرشاد الحكومي المناسب</div>`;
        }

        const followup = agentState.currentHint && !agentState.isLoading ? `
            <div style="padding:8px;border-top:1px solid #243460;display:flex;gap:6px;flex-shrink:0">
                <input type="text" data-role="followup"
                    value="${escapeHtml(this._followup)}"
                    placeholder="سؤال متابعة..." dir="rtl"
                    style="flex:1;background:#243460;border:1px solid #355080;color:#f0f4ff;
                        padding:6px 8px;border-radius:3px;font-family:inherit;font-size:12px;outline:none"/>
                <button data-action="send" style="
                    background:#c8a84b;color:#1a2744;border:none;padding:6px 12px;
                    border-radius:3px;cursor:pointer;font-family:inherit;font-size:12px;
                    font-weight:600">إرسال</button>
            </div>` : "";

        return `
            <div style="display:flex;align-items:center;gap:8px;padding:10px 12px;
                background:#1a2744;border-bottom:1px solid #243460;flex-shrink:0;min-height:50px">
                <svg viewBox="0 0 40 40" width="30" height="30" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0">
                    <circle cx="20" cy="20" r="18" fill="#c8a84b" stroke="#1a2744" stroke-width="2"/>
                    <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle"
                        font-size="16" fill="#1a2744" font-weight="bold">م</text>
                </svg>
                <div style="flex:1;display:flex;align-items:center">
                    ${dot}
                    <span style="font-size:13px;font-weight:700;color:#c8a84b">المرشد الحكومي</span>
                </div>
                <button data-action="toggle" style="
                    background:transparent;border:none;color:#c8a84b;
                    cursor:pointer;font-size:16px;padding:4px 8px;line-height:1">&#x25BA;</button>
            </div>
            <div style="padding:5px 12px;background:#243460;font-size:11px;color:#9bacc8;flex-shrink:0">
                الحقل: <span style="color:#f0f4ff">${escapeHtml(field)}</span>
            </div>
            <div style="flex:1;overflow-y:auto">${hintArea}</div>
            ${followup}
            <div style="padding:5px 12px;border-top:1px solid #243460;font-size:10px;
                color:#9bacc8;text-align:center;flex-shrink:0">المرشد الحكومي الذكي</div>`;
    }

    _handleClick(e) {
        const action = e.target.closest("[data-action]")?.dataset?.action;
        if (action === "toggle") {
            this._expanded = !this._expanded;
            this._render();
        } else if (action === "copy") {
            const text = agentState.currentHint;
            if (!text) return;
            navigator.clipboard?.writeText(text).catch(() => {
                const ta = document.createElement("textarea");
                ta.value = text; document.body.appendChild(ta);
                ta.select(); document.execCommand("copy");
                document.body.removeChild(ta);
            });
            this._copyOk = true; this._render();
            setTimeout(() => { this._copyOk = false; this._render(); }, 2000);
        } else if (action === "send") {
            this._sendFollowup();
        }
    }

    async _sendFollowup() {
        const q = this._followup.trim();
        if (!q) return;
        this._followup = "";
        if (this._connector) {
            try { await this._connector.sendFollowup(q); } catch (_e) {}
        }
    }

    destroy() {
        clearInterval(this._intervalId);
        this._el?.remove();
    }
}

// ─── Service — لا systray، لا OWL component ──────────────────────────────────

const govSidebarService = {
    name: "gov_ai_sidebar_ui",
    dependencies: [],
    start(env, services) {
        // ننتظر اكتمال تحميل الصفحة قبل الحقن
        const init = () => {
            if (document.getElementById("gov-ai-sidebar-root")) return;
            try {
                const connector = env.services?.gov_ai_agent_connector || null;
                const sidebar = new GovSidebar(connector);
                sidebar.mount();
            } catch (_e) {}
        };

        if (document.readyState === "complete") {
            setTimeout(init, 500);
        } else {
            window.addEventListener("load", () => setTimeout(init, 500));
        }
    },
};

registry.category("services").add("gov_ai_sidebar_ui", govSidebarService);
