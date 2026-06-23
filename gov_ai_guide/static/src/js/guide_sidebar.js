/** @odoo-module **/

import { Component, useState, useEffect, markup, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { agentState } from "./agent_connector";

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function parseHintText(text) {
    if (!text) return { html: "", lawRefs: [], warnings: [] };
    const lawRefs = [];
    const lawPattern = /(?:قانون|لائحة|قرار|معيار|مرسوم)\s+(?:رقم\s+)?(?:وزاري\s+)?[\d٠-٩]+\/[\d٠-٩]+/g;
    let match;
    while ((match = lawPattern.exec(text)) !== null) {
        if (!lawRefs.includes(match[0])) lawRefs.push(match[0]);
    }
    const lines = text.split("\n");
    const html = lines.map((line) => {
        if (line.includes("⚠") || /^تنبيه/i.test(line.trim())) {
            return `<span style="color:#e53935">${escapeHtml(line)}</span>`;
        }
        return escapeHtml(line)
            .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
            .replace(
                /((?:قانون|لائحة|قرار|معيار|مرسوم)\s+(?:رقم\s+)?(?:وزاري\s+)?[\d٠-٩]+\/[\d٠-٩]+)/g,
                '<span style="background:#c8a84b;color:#1a2744;padding:1px 5px;border-radius:3px;font-size:11px">$1</span>'
            );
    }).join("<br/>");
    return { html, lawRefs, warnings: [] };
}

export class GovAISidebar extends Component {
    static template = "gov_ai_guide.GovAISidebar";
    static props = {};

    setup() {
        this.state = useState({
            expanded: true,
            followupText: "",
            copyOk: false,
            parsed: { html: "", lawRefs: [] },
        });

        this._connector = null;

        onMounted(() => {
            try {
                this._connector =
                    this.__owl__.app?.env?.services?.gov_ai_agent_connector || null;
            } catch (_e) {
                this._connector = null;
            }
        });

        useEffect(
            () => {
                try {
                    this.state.parsed = parseHintText(agentState.currentHint || "");
                } catch (_e) {}
            },
            () => [agentState.currentHint, agentState.isStreaming]
        );
    }

    get agentState() { return agentState; }

    get renderedHint() {
        try { return markup(this.state.parsed.html || ""); }
        catch (_e) { return markup(""); }
    }

    get fieldLabel() {
        const f = agentState.currentField;
        if (!f) return "انتظر تركيز أي حقل...";
        return f.replace(/_/g, " ");
    }

    get showLoader() {
        return agentState.isLoading || agentState.isStreaming;
    }

    toggleSidebar() {
        this.state.expanded = !this.state.expanded;
    }

    async copyHint() {
        const text = agentState.currentHint;
        if (!text) return;
        try {
            await navigator.clipboard.writeText(text);
        } catch (_e) {
            const ta = document.createElement("textarea");
            ta.value = text;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
        }
        this.state.copyOk = true;
        setTimeout(() => { this.state.copyOk = false; }, 2000);
    }

    async sendFollowup() {
        const q = this.state.followupText.trim();
        if (!q || !this._connector) return;
        this.state.followupText = "";
        try { await this._connector.sendFollowup(q); } catch (_e) {}
    }

    onFollowupKey(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendFollowup();
        }
    }
}

registry.category("systray").add("gov_ai_sidebar", {
    Component: GovAISidebar,
    sequence: 1,
});
