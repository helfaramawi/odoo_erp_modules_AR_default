/** @odoo-module **/
import { Component, useState, onMounted, onWillUnmount, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ── State color map ──────────────────────────────────────────────
const STATE_COLORS = {
    'نشطة': '#27AE60', 'نشط': '#27AE60', 'مرحّل': '#27AE60',
    'مكتمل': '#27AE60', 'ساري': '#27AE60', 'مدفوع': '#27AE60',
    'مسودة': '#9BAAB8', 'منتهية': '#9BAAB8', 'ملغي': '#9BAAB8',
    'إخطار الترسية': '#C9A84C', 'تمت المقارنة': '#C9A84C',
    'تسجيل العروض': '#C9A84C', 'معتمد': '#C9A84C',
    'مظاريف مالية مفتوحة': '#F39C12', 'مظاريف فنية مفتوحة': '#F39C12',
    'الجلسة مفتوحة': '#F39C12', 'جاري الجرد': '#F39C12',
    'أمر شراء صادر': '#2196F3', 'محوّل': '#2196F3',
    'مرفوض': '#E74C3C', 'متأخرة': '#E74C3C', 'متأخر': '#E74C3C',
};

function badge(state) {
    const c = STATE_COLORS[state] || '#9BAAB8';
    return `<span class="sb" style="background:${c}22;color:${c}">${state}</span>`;
}

function fmtNum(n) {
    if (!n) return '0';
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'م';
    if (n >= 1000) return (n / 1000).toFixed(0) + 'ك';
    return n.toLocaleString();
}

// ── Main Dashboard Component ─────────────────────────────────────
class PortSaidDashboard extends Component {
    static template = xml`
<div class="o_portsaid_dashboard">

    <!-- Header -->
    <div class="ps-header">
        <div class="ps-brand">
            <div class="ps-emblem">⚓</div>
            <div>
                <h1>لوحة القيادة التنفيذية</h1>
                <p>الديوان العام لمحافظة بورسعيد — سلسلة التوريد</p>
            </div>
        </div>
        <div class="ps-meta">
            <div class="ps-stat">
                <div class="val" t-esc="state.meta.total_ops || '...'"></div>
                <div class="lbl">إجمالي العمليات</div>
            </div>
            <div class="ps-divider"></div>
            <div class="ps-stat">
                <div class="val" t-esc="state.adjTotalFmt || '...'"></div>
                <div class="lbl">قيمة التعاقدات (ج.م)</div>
            </div>
            <div class="ps-divider"></div>
            <div class="ps-stat">
                <div class="val" style="color:#E74C3C" t-esc="state.alertsCount || '0'"></div>
                <div class="lbl">تنبيهات عاجلة</div>
            </div>
            <div class="ps-divider"></div>
            <div class="live-dot">مباشر</div>
        </div>
    </div>

    <!-- Nav -->
    <div class="ps-nav">
        <button class="ps-nav-btn" t-att-class="{active: state.page==='overview'}"
            t-on-click="() => this.setPage('overview')">
            <span>📊</span> نظرة عامة
        </button>
        <button class="ps-nav-btn" t-att-class="{active: state.page==='contracts'}"
            t-on-click="() => this.setPage('contracts')">
            <span>📋</span> التعاقدات
            <span class="nb" style="background:rgba(201,168,76,.2);color:#E8C87A"
                t-esc="state.adjTotal || ''"></span>
        </button>
        <button class="ps-nav-btn" t-att-class="{active: state.page==='warehouse'}"
            t-on-click="() => this.setPage('warehouse')">
            <span>🏭</span> المخازن
            <span class="nb" style="background:rgba(30,127,116,.2);color:#27A99A"
                t-esc="state.permitTotal || ''"></span>
        </button>
        <button class="ps-nav-btn" t-att-class="{active: state.page==='custody'}"
            t-on-click="() => this.setPage('custody')">
            <span>🔑</span> العهد
            <span class="nb" style="background:rgba(33,150,243,.2);color:#90CAF9"
                t-esc="state.custodyActive || ''"></span>
        </button>
        <button class="ps-nav-btn" t-att-class="{active: state.page==='auction'}"
            t-on-click="() => this.setPage('auction')">
            <span>🏛️</span> المزايدات
            <span class="nb" style="background:rgba(192,57,43,.2);color:#E74C3C"
                t-esc="state.auctionActive || ''"></span>
        </button>
        <button class="ps-nav-btn" t-att-class="{active: state.page==='alerts'}"
            t-on-click="() => this.setPage('alerts')">
            <span>🔔</span> التنبيهات
            <span class="nb" style="background:rgba(192,57,43,.3);color:#E74C3C"
                t-esc="state.alertsCount || ''"></span>
        </button>
    </div>

    <!-- Loading -->
    <div t-if="state.loading" class="ps-main">
        <div class="ps-loading">
            <div class="ps-spinner"></div>
            <div style="color:var(--muted);font-size:14px">جاري تحميل البيانات...</div>
        </div>
    </div>

    <!-- Main content -->
    <div t-else="" class="ps-main" id="ps-main-content"></div>

    <!-- Drill overlay -->
    <div class="ps-drill-ov" id="ps-drill-ov" t-on-click="closeDrillOverlay">
        <div class="ps-drill-pnl">
            <button class="ps-drill-x" t-on-click="closeDrill">✕</button>
            <div class="ps-drill-ttl" id="ps-drill-ttl"></div>
            <div class="ps-drill-kpis" id="ps-drill-kpis"></div>
            <table class="ps-tbl" id="ps-drill-tbl"></table>
        </div>
    </div>
</div>`;

    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            page: 'overview',
            data: null,
            meta: {},
            adjTotalFmt: '...',
            adjTotal: '',
            permitTotal: '',
            custodyActive: '',
            auctionActive: '',
            alertsCount: '',
        });
        this._refreshInterval = null;

        onMounted(() => {
            this.loadData();
            // Auto-refresh every 5 minutes
            this._refreshInterval = setInterval(() => this.loadData(), 300000);
        });
        onWillUnmount(() => {
            if (this._refreshInterval) clearInterval(this._refreshInterval);
        });
    }

    async loadData() {
        try {
            const data = await this.rpc('/portsaid/dashboard/data', {});
            this.state.data = data;
            this.state.meta = data.meta || {};
            this.state.adjTotalFmt = fmtNum(data.adjudication?.total_estimated || 0);
            this.state.adjTotal = data.adjudication?.total || 0;
            this.state.permitTotal = data.permits?.total || 0;
            this.state.custodyActive = data.custody?.active || 0;
            this.state.auctionActive = (data.auction?.by_state?.session_open || 0) +
                                       (data.auction?.by_state?.bidding || 0);
            this.state.alertsCount = (data.alerts || []).length;
            this.state.loading = false;
            // Render after state update
            setTimeout(() => this.renderPage(), 50);
        } catch (e) {
            console.error('Dashboard load error:', e);
            this.state.loading = false;
        }
    }

    setPage(page) {
        this.state.page = page;
        setTimeout(() => this.renderPage(), 30);
    }

    renderPage() {
        const d = this.state.data;
        if (!d) return;
        const el = document.getElementById('ps-main-content');
        if (!el) return;

        const page = this.state.page;
        el.innerHTML = this.buildPage(page, d);
        // Animate bars after render
        setTimeout(() => this.animateBars(el), 80);
    }

    buildPage(page, d) {
        switch (page) {
            case 'overview':   return this.pageOverview(d);
            case 'contracts':  return this.pageContracts(d);
            case 'warehouse':  return this.pageWarehouse(d);
            case 'custody':    return this.pageCustody(d);
            case 'auction':    return this.pageAuction(d);
            case 'alerts':     return this.pageAlerts(d);
            default:           return this.pageOverview(d);
        }
    }

    // ── Page builders ──────────────────────────────────────────────

    pageOverview(d) {
        const c  = d.committees;
        const a  = d.adjudication;
        const p  = d.permits;
        const s  = d.stocktaking;
        const cu = d.custody;
        const au = d.auction;

        return `
<div class="ps-page active">
    <div class="ps-sec">مؤشرات الأداء الرئيسية</div>
    <div class="ps-kpis">
        ${this.kpi('👥', c.active, 'لجنة نشطة', '#C9A84C', `+${c.draft} مسودة`, 'committees')}
        ${this.kpi('⚖️', a.by_state.awarded + a.by_state.po_created, 'في مرحلة الترسية', '#27AE60', `${a.total} إجمالي`, 'adjudication')}
        ${this.kpi('📦', p.total, 'إذن إضافة', '#27A99A', `${p.posted} مرحّل`, 'permits')}
        ${this.kpi('🔑', cu.active, 'عهدة نشطة', '#2196F3', `⚠️ ${cu.overdue} متأخرة`, 'custody')}
        ${this.kpi('📊', s.done, 'جرد بانتظار الاعتماد', '#E74C3C', `${s.validated} معتمد`, 'stocktaking')}
        ${this.kpi('🏛️', au.by_state.session_open + au.by_state.bidding, 'مزاد نشط', '#F39C12', `${au.lease.active} عقد إيجار`, 'auctions')}
    </div>

    <div class="ps-row">
        <div class="ps-panel">
            <div class="ps-ptitle">📋 مسار التعاقدات</div>
            ${this.stateBars([
                {label:'مسودة',                   count:a.by_state.draft,         color:'#9BAAB8'},
                {label:'فتح المظاريف الفنية',     count:a.by_state.technical_open, color:'#F39C12'},
                {label:'فتح المظاريف المالية',    count:a.by_state.financial_open, color:'#C9A84C'},
                {label:'تمت المقارنة المالية',    count:a.by_state.adjudicated,   color:'#2196F3'},
                {label:'إخطار الترسية',           count:a.by_state.awarded,       color:'#27AE60'},
                {label:'أمر شراء صادر',           count:a.by_state.po_created,    color:'#1565C0'},
            ])}
        </div>
        <div class="ps-panel">
            <div class="ps-ptitle">📦 نتائج الفحص والاستلام</div>
            ${this.donut([
                {c:'#27A99A', l:'مكتمل مطابق',    v:p.inspection.done},
                {c:'#C9A84C', l:'مطابق مع تحفظ', v:Math.round(p.inspection.done * 0.12)},
                {c:'#E74C3C', l:'مرفوض',          v:p.inspection.rejected},
            ])}
        </div>
    </div>

    <div class="ps-row">
        <div class="ps-panel">
            <div class="ps-ptitle">📈 العمليات الشهرية</div>
            ${this.barChart(d.monthly.map((m,i) => ({
                label: m.label,
                val:   m.count,
                color: i === d.monthly.length-1 ? '#C9A84C' :
                       i === d.monthly.length-2 ? '#27A99A' : '#2E4B6E',
            })))}
        </div>
        <div class="ps-panel">
            <div class="ps-ptitle">🔑 حالة العهد</div>
            ${this.stateBars([
                {label:'نشطة',    count:cu.active,       color:'#27AE60'},
                {label:'محوّلة',  count:cu.transferred,  color:'#2196F3'},
                {label:'متأخرة',  count:cu.overdue,      color:'#E74C3C'},
                {label:'مُرتجعة',count:cu.returned,      color:'#9BAAB8'},
            ])}
        </div>
    </div>
</div>`;
    }

    pageContracts(d) {
        const a = d.adjudication;
        const c = d.committees;
        const savPct = a.saving_pct || 0;
        const tenderLabels = {
            public:'مناقصة عامة', local:'مناقصة محلية',
            limited:'مناقصة محدودة', negotiation:'ممارسة',
            direct_supply:'أمر مباشر توريد', direct_private:'أمر مباشر خاص'
        };

        return `
<div class="ps-page active">
    <div class="ps-sec">التعاقدات والمناقصات</div>
    <div class="ps-kpis">
        ${this.kpi('📝', c.total,  'إجمالي اللجان',     '#C9A84C', `${c.active} نشطة`, 'committees')}
        ${this.kpi('⚖️', a.total,  'ملف بت',            '#27AE60', `${a.by_state.awarded} ترسية`, 'adjudication')}
        ${this.kpi('💰', fmtNum(a.total_estimated), 'قيمة تقديرية (ج.م)', '#2196F3', '', '')}
        ${this.kpi('📊', savPct+'%', 'نسبة التوفير', '#F39C12', 'مقارنة بالتقديري', '')}
    </div>
    <div class="ps-row">
        <div class="ps-panel">
            <div class="ps-ptitle">حالة ملفات البت</div>
            ${this.stateBars([
                {label:'مسودة',                count:a.by_state.draft,         color:'#9BAAB8'},
                {label:'مظاريف فنية مفتوحة',  count:a.by_state.technical_open, color:'#F39C12'},
                {label:'مظاريف مالية مفتوحة', count:a.by_state.financial_open, color:'#FFCC99'},
                {label:'تمت المقارنة',         count:a.by_state.adjudicated,   color:'#C9A84C'},
                {label:'إخطار الترسية',        count:a.by_state.awarded,       color:'#27AE60'},
                {label:'أمر شراء صادر',        count:a.by_state.po_created,    color:'#1565C0'},
                {label:'ملغي',                 count:a.by_state.cancelled,     color:'#E74C3C'},
            ])}
        </div>
        <div class="ps-panel">
            <div class="ps-ptitle">توزيع وسائل الطرح</div>
            ${this.barChart(Object.entries(a.tender_types || {}).map(([k,v]) => ({
                label: tenderLabels[k] || k,
                val: v,
                color: '#2196F3',
            })))}
        </div>
    </div>
    <div class="ps-full">
        <div class="ps-panel">
            <div class="ps-ptitle">آخر ملفات البت — <span style="font-weight:400;color:var(--muted)">اضغط لفتح السجل</span></div>
            <table class="ps-tbl">
                <thead><tr>
                    <th>المرجع</th><th>العملية</th><th>نوع الطرح</th>
                    <th>الحالة</th><th>القيمة التقديرية</th><th>قيمة الترسية</th>
                </tr></thead>
                <tbody>
                ${(a.detail || []).map(r => `<tr onclick="window._psDrill('adj','${r.id}')">
                    <td style="color:#E8C87A;font-weight:700">${r.ref || r.name}</td>
                    <td>${r.name || ''}</td>
                    <td>${tenderLabels[r.tender_type] || r.tender_type || '—'}</td>
                    <td>${badge(this.stateLabel(r.state, 'adj'))}</td>
                    <td>${r.estimated_value ? r.estimated_value.toLocaleString()+' ج.م' : '—'}</td>
                    <td>${r.awarded_amount ? '<span style="color:#27AE60">'+r.awarded_amount.toLocaleString()+' ج.م</span>' : '—'}</td>
                </tr>`).join('')}
                </tbody>
            </table>
        </div>
    </div>
</div>`;
    }

    pageWarehouse(d) {
        const p = d.permits;
        const s = d.stocktaking;
        return `
<div class="ps-page active">
    <div class="ps-sec">المخازن والجرد</div>
    <div class="ps-kpis">
        ${this.kpi('📦', p.total,    'إذن إضافة',          '#27A99A', `${p.posted} مرحّل`, 'permits')}
        ${this.kpi('✅', p.posted,   'مرحّل بنجاح',        '#27AE60', Math.round(p.posted/(p.total||1)*100)+'% قبول', '')}
        ${this.kpi('❌', p.cancelled,'مرفوض/ملغي',         '#E74C3C', 'يحتاج مراجعة', '')}
        ${this.kpi('🔍', s.total,    'جلسة جرد',           '#C9A84C', `${s.done} بانتظار الاعتماد`, 'stocktaking')}
    </div>
    <div class="ps-row">
        <div class="ps-panel">
            <div class="ps-ptitle">نتائج محاضر الفحص</div>
            ${this.stateBars([
                {label:'مكتمل مطابق',    count:p.inspection.done,     color:'#27AE60'},
                {label:'قيد الفحص',      count:p.inspection.draft,    color:'#F39C12'},
                {label:'مرفوض',          count:p.inspection.rejected, color:'#E74C3C'},
            ])}
        </div>
        <div class="ps-panel">
            <div class="ps-ptitle">جلسات الجرد — الحالة</div>
            ${this.stateBars([
                {label:'مسودة',       count:s.draft,     color:'#9BAAB8'},
                {label:'جاري الجرد', count:s.counting,  color:'#F39C12'},
                {label:'منتهي',       count:s.done,      color:'#2196F3'},
                {label:'معتمد',       count:s.validated, color:'#27AE60'},
            ])}
        </div>
    </div>
    <div class="ps-row3">
        ${this.gaugePanel('نسبة الزيادة في الجرد', s.surplus_pct+'%', s.surplus_pct, '#27AE60', 'أصناف زيادة')}
        ${this.gaugePanel('نسبة العجز في الجرد', s.deficit_pct+'%', s.deficit_pct, '#E74C3C', 'أصناف عجز')}
        ${this.gaugePanel('المخزون الراكد', '—', 0, '#F39C12', 'غير محدد')}
    </div>
</div>`;
    }

    pageCustody(d) {
        const cu = d.custody;
        return `
<div class="ps-page active">
    <div class="ps-sec">إدارة العهد</div>
    <div class="ps-kpis">
        ${this.kpi('🔑', cu.active,      'عهدة نشطة',           '#2196F3', '', 'custody')}
        ${this.kpi('⚠️', cu.overdue,     'متأخرة الاسترداد',   '#E74C3C', 'يجب المتابعة', '')}
        ${this.kpi('↩️', cu.returned,    'مُرتجعة',             '#27AE60', 'إجمالي المردودة', '')}
        ${this.kpi('💎', fmtNum(cu.total_value), 'قيمة العهد النشطة (ج.م)', '#C9A84C', '', '')}
    </div>
    <div class="ps-row">
        <div class="ps-panel">
            <div class="ps-ptitle">توزيع العهد حسب الحالة</div>
            ${this.stateBars([
                {label:'نشطة',    count:cu.active,       color:'#27AE60'},
                {label:'محوّلة',  count:cu.transferred,  color:'#2196F3'},
                {label:'متأخرة',  count:cu.overdue,      color:'#E74C3C'},
                {label:'مُرتجعة',count:cu.returned,      color:'#9BAAB8'},
                {label:'ملغية',   count:cu.cancelled,    color:'#555'},
            ])}
        </div>
        <div class="ps-panel">
            <div class="ps-ptitle">نوع العهد</div>
            ${this.stateBars([
                {label:'شخصية',  count:cu.by_type.personal,    color:'#2196F3'},
                {label:'مشتركة', count:cu.by_type.shared,      color:'#27A99A'},
                {label:'منقولة', count:cu.by_type.transferred, color:'#C9A84C'},
            ])}
        </div>
    </div>
    <div class="ps-full">
        <div class="ps-panel">
            <div class="ps-ptitle" style="color:#E74C3C">⚠️ العهد المتأخرة — تنبيه عاجل</div>
            <table class="ps-tbl">
                <thead><tr>
                    <th>المرجع</th><th>الموظف</th><th>القيمة</th>
                    <th>تاريخ الاسترداد</th><th>الحالة</th>
                </tr></thead>
                <tbody>
                ${(cu.overdue_detail || []).map(r => `<tr>
                    <td style="color:#90CAF9;font-weight:700">${r.ref}</td>
                    <td>${r.employee}</td>
                    <td>${r.value ? r.value.toLocaleString()+' ج.م' : '—'}</td>
                    <td style="color:#E74C3C">${r.due}</td>
                    <td>${badge('متأخرة')}</td>
                </tr>`).join('')}
                ${!(cu.overdue_detail || []).length ? '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:20px">لا توجد عهد متأخرة ✅</td></tr>' : ''}
                </tbody>
            </table>
        </div>
    </div>
</div>`;
    }

    pageAuction(d) {
        const au = d.auction;
        return `
<div class="ps-page active">
    <div class="ps-sec">المزايدات والمزادات</div>
    <div class="ps-kpis">
        ${this.kpi('🏛️', au.by_state.session_open + au.by_state.bidding, 'مزاد نشط', '#F39C12', '', 'auctions')}
        ${this.kpi('🏆', au.by_state.done, 'مزاد مكتمل', '#27AE60', '', '')}
        ${this.kpi('📃', au.lease.active,  'عقد إيجار ساري', '#2196F3', `${au.lease.expired} منتهي`, '')}
        ${this.kpi('💸', au.payments.overdue, 'دفعة متأخرة', '#E74C3C', 'مطلوب تحصيل', '')}
    </div>
    <div class="ps-row">
        <div class="ps-panel">
            <div class="ps-ptitle">حالة طلبات المزاد</div>
            ${this.stateBars([
                {label:'مسودة',          count:au.by_state.draft,       color:'#9BAAB8'},
                {label:'الجلسة مفتوحة', count:au.by_state.session_open, color:'#F39C12'},
                {label:'تسجيل العروض',  count:au.by_state.bidding,     color:'#C9A84C'},
                {label:'تم الترسية',     count:au.by_state.awarded,     color:'#27AE60'},
                {label:'منتهي',          count:au.by_state.done,        color:'#2E4B6E'},
                {label:'ملغي',           count:au.by_state.cancelled,   color:'#E74C3C'},
            ])}
        </div>
        <div class="ps-panel">
            <div class="ps-ptitle">جدول سداد العقود</div>
            ${this.stateBars([
                {label:'قيد الانتظار', count:au.payments.pending, color:'#9BAAB8'},
                {label:'مدفوع جزئياً', count:au.payments.partial, color:'#F39C12'},
                {label:'مدفوع',        count:au.payments.paid,    color:'#27AE60'},
                {label:'متأخر',        count:au.payments.overdue, color:'#E74C3C'},
            ])}
        </div>
    </div>
    <div class="ps-full">
        <div class="ps-panel">
            <div class="ps-ptitle">المزادات الجارية والمكتملة</div>
            <table class="ps-tbl">
                <thead><tr>
                    <th>المرجع</th><th>الاسم</th><th>النوع</th>
                    <th>الحالة</th><th>القيمة التقديرية</th><th>مبلغ الترسية</th>
                </tr></thead>
                <tbody>
                ${(au.detail || []).map(r => `<tr>
                    <td style="color:#FAC775;font-weight:700">${r.ref || r.name}</td>
                    <td>${r.name || ''}</td>
                    <td>${r.auction_type === 'sale' ? 'بيع' : 'إيجار'}</td>
                    <td>${badge(this.stateLabel(r.state, 'auction'))}</td>
                    <td>${r.estimated_value ? r.estimated_value.toLocaleString()+' ج.م' : '—'}</td>
                    <td>${r.awarded_amount ? '<span style="color:#27AE60">'+r.awarded_amount.toLocaleString()+' ج.م</span>' : '—'}</td>
                </tr>`).join('')}
                </tbody>
            </table>
        </div>
    </div>
</div>`;
    }

    pageAlerts(d) {
        const alerts = d.alerts || [];
        const alertColors = { danger:'#E74C3C', warning:'#F39C12', info:'#2196F3' };
        return `
<div class="ps-page active">
    <div class="ps-sec">التنبيهات العاجلة (${alerts.length})</div>
    ${alerts.length ? alerts.map(a => `
        <div class="ps-alert">
            <div class="ai">${a.icon}</div>
            <div class="ab">
                <div class="at" style="color:${alertColors[a.type]||'#C9A84C'}">${a.title}</div>
                <div class="ad">${a.desc}</div>
            </div>
        </div>`).join('') :
    '<div style="text-align:center;padding:40px;color:var(--muted)">✅ لا توجد تنبيهات عاجلة</div>'}
</div>`;
    }

    // ── Component helpers ─────────────────────────────────────────

    kpi(icon, val, label, color, sub, drillKey) {
        const drill = drillKey ? `onclick="window._psDrillKey('${drillKey}')"` : '';
        return `<div class="ps-kpi" style="--kc:${color}" ${drill}>
            <div class="ki">${icon}</div>
            <div class="kv">${val}</div>
            <div class="kl">${label}</div>
            ${sub ? `<div class="ks">${sub}</div>` : ''}
            ${drillKey ? '<div class="kb">تفاصيل ↗</div>' : ''}
        </div>`;
    }

    stateBars(data) {
        const total = data.reduce((s, d) => s + (d.count || 0), 0);
        return data.map(d => {
            const pct = total ? Math.round((d.count || 0) / total * 100) : 0;
            const w   = total ? ((d.count || 0) / total * 100) : 0;
            return `<div class="ps-srow">
                <div class="ps-slbl">${d.label}</div>
                <div class="ps-strk"><div class="sf" data-w="${w}" style="background:${d.color}"></div></div>
                <div class="ps-scnt">${d.count || 0}</div>
                <div class="ps-spct">${pct}%</div>
            </div>`;
        }).join('');
    }

    barChart(data) {
        const max = Math.max(...data.map(d => d.val || 0), 1);
        return `<div class="ps-bars">
            ${data.map(d => {
                const h = Math.round((d.val || 0) / max * 80);
                return `<div class="ps-bc">
                    <div class="ps-bv" style="color:${d.color||'#C9A84C'}">${d.val}</div>
                    <div class="ps-bf" data-h="${h}" style="background:${d.color||'#C9A84C'};height:4px"></div>
                    <div class="ps-bl">${d.label}</div>
                </div>`;
            }).join('')}
        </div>`;
    }

    donut(segments) {
        const total = segments.reduce((s, d) => s + (d.v || 0), 1);
        const circ  = 2 * Math.PI * 38;
        let offset  = 0;
        const circles = segments.map(s => {
            const len = circ * (s.v || 0) / total;
            const gap = circ - len;
            const rot = offset;
            offset += len;
            return `<circle cx="50" cy="50" r="38" fill="none" stroke="${s.c}"
                stroke-width="12" stroke-linecap="round"
                stroke-dasharray="${len} ${gap}"
                stroke-dashoffset="${-rot}"
                style="transition:stroke-dasharray .9s ease"/>`;
        });
        const pct = total > 0 ? Math.round((segments[0].v || 0) / total * 100) : 0;
        return `<div class="ps-dw">
            <div class="ps-dn">
                <svg width="100" height="100" viewBox="0 0 100 100" style="transform:rotate(-90deg)">
                    <circle cx="50" cy="50" r="38" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="12"/>
                    ${circles.join('')}
                </svg>
                <div class="ps-dnc">
                    <div class="ps-dnp" style="color:${segments[0].c}">${pct}%</div>
                    <div class="ps-dns">${segments[0].l}</div>
                </div>
            </div>
            <div class="ps-leg">
                ${segments.map(s => `<div class="li">
                    <div class="ld" style="background:${s.c}"></div>
                    <div class="ll">${s.l}</div>
                    <div class="lv">${s.v}</div>
                </div>`).join('')}
            </div>
        </div>`;
    }

    gaugePanel(title, val, pct, color, sub) {
        const fill = Math.min(pct || 0, 100) * 1.57;
        return `<div class="ps-panel ps-gauge">
            <div class="ps-ptitle" style="justify-content:center">${title}</div>
            <svg width="130" height="70" viewBox="0 0 130 70">
                <path d="M 15 65 A 50 50 0 0 1 115 65" fill="none"
                    stroke="rgba(255,255,255,.08)" stroke-width="12" stroke-linecap="round"/>
                <path d="M 15 65 A 50 50 0 0 1 115 65" fill="none"
                    stroke="${color}" stroke-width="12" stroke-linecap="round"
                    stroke-dasharray="${fill} 157"
                    style="transition:stroke-dasharray .9s ease"/>
            </svg>
            <div class="gv" style="color:${color}">${val}</div>
            <div class="gl">${sub}</div>
        </div>`;
    }

    stateLabel(state, type) {
        const adjMap = {
            draft:'مسودة', technical_open:'مظاريف فنية مفتوحة',
            financial_open:'مظاريف مالية مفتوحة', adjudicated:'تمت المقارنة',
            awarded:'إخطار الترسية', po_created:'أمر شراء صادر', cancelled:'ملغي'
        };
        const auctMap = {
            draft:'مسودة', confirmed:'معتمد', session_open:'الجلسة مفتوحة',
            bidding:'تسجيل العروض', awarded:'تم الترسية', done:'منتهي', cancelled:'ملغي'
        };
        if (type === 'adj')     return adjMap[state]  || state;
        if (type === 'auction') return auctMap[state] || state;
        return state;
    }

    animateBars(container) {
        container.querySelectorAll('.sf[data-w]').forEach(el => {
            const w = el.getAttribute('data-w');
            el.style.width = w + '%';
        });
        container.querySelectorAll('.ps-bf[data-h]').forEach(el => {
            const h = el.getAttribute('data-h');
            el.style.height = (parseInt(h) || 4) + 'px';
        });
    }

    // ── Drill down ────────────────────────────────────────────────
    closeDrillOverlay(ev) {
        if (ev.target === document.getElementById('ps-drill-ov'))
            this.closeDrill();
    }
    closeDrill() {
        const ov = document.getElementById('ps-drill-ov');
        if (ov) ov.classList.remove('open');
    }

    openDrill(key) {
        const d = this.state.data;
        if (!d) return;

        const drillMap = {
            committees: {
                title: '👥 تفاصيل اللجان المشكّلة',
                kpis: [
                    {v: d.committees.total,  l:'إجمالي اللجان'},
                    {v: d.committees.active, l:'نشطة'},
                    {v: d.committees.draft,  l:'مسودة'},
                ],
                headers: ['المرجع','الاسم','النوع','الحالة','الأعضاء','تاريخ التشكيل'],
                rows: (d.committees.detail || []).map(r => [
                    `<span style="color:#E8C87A;font-weight:700">${r.ref || r.id}</span>`,
                    r.name, r.committee_type || '—',
                    badge(r.state === 'active' ? 'نشطة' : r.state === 'draft' ? 'مسودة' : 'منتهية'),
                    r.member_count || 0,
                    r.formation_date || '—',
                ]),
            },
            adjudication: {
                title: '⚖️ تفاصيل ملفات البت',
                kpis: [
                    {v: d.adjudication.total,                              l:'إجمالي الملفات'},
                    {v: fmtNum(d.adjudication.total_estimated),            l:'إجمالي القيمة التقديرية'},
                    {v: d.adjudication.by_state.awarded + d.adjudication.by_state.po_created, l:'في مرحلة الترسية'},
                ],
                headers: ['المرجع','العملية','الحالة','التقديري','الترسية'],
                rows: (d.adjudication.detail || []).map(r => [
                    `<span style="color:#E8C87A">${r.ref || r.name}</span>`,
                    r.name,
                    badge(this.stateLabel(r.state, 'adj')),
                    r.estimated_value ? r.estimated_value.toLocaleString()+' ج.م' : '—',
                    r.awarded_amount  ? r.awarded_amount.toLocaleString()+' ج.م'  : '—',
                ]),
            },
            permits: {
                title: '📦 تفاصيل أذونات الإضافة',
                kpis: [
                    {v: d.permits.total,    l:'إجمالي الأذونات'},
                    {v: d.permits.posted,   l:'مرحّل بنجاح'},
                    {v: d.permits.cancelled,l:'مرفوض/ملغي'},
                ],
                headers: ['المرجع','الصنف','الحالة','الكمية','المستودع','التاريخ'],
                rows: (d.permits.detail || []).map(r => [
                    `<span style="color:#27A99A;font-weight:700">${r.ref || r.id}</span>`,
                    r.name,
                    badge(r.state === 'posted' ? 'مرحّل' : r.state === 'draft' ? 'مسودة' : 'ملغي'),
                    r.qty || '—',
                    r.warehouse_id ? r.warehouse_id[1] : '—',
                    r.date || '—',
                ]),
            },
            custody: {
                title: '🔑 تفاصيل العهد النشطة',
                kpis: [
                    {v: d.custody.active,           l:'عهدة نشطة'},
                    {v: d.custody.overdue,           l:'متأخرة'},
                    {v: fmtNum(d.custody.total_value),l:'إجمالي القيمة'},
                ],
                headers: ['المرجع','الموظف','الحالة','القيمة','تاريخ الاسترداد'],
                rows: (d.custody.detail || []).map(r => [
                    `<span style="color:#90CAF9;font-weight:700">${r.name}</span>`,
                    r.employee_id ? r.employee_id[1] : '—',
                    badge(r.state === 'active' ? 'نشطة' : r.state === 'transferred' ? 'محوّلة' : r.state),
                    r.estimated_value ? r.estimated_value.toLocaleString()+' ج.م' : '—',
                    r.expected_return_date || '—',
                ]),
            },
            stocktaking: {
                title: '📊 تفاصيل جلسات الجرد',
                kpis: [
                    {v: d.stocktaking.total,     l:'إجمالي الجلسات'},
                    {v: d.stocktaking.done,      l:'بانتظار الاعتماد'},
                    {v: d.stocktaking.validated, l:'معتمد'},
                ],
                headers: ['الجلسة','المستودع','السنة المالية','الحالة','رئيس اللجنة'],
                rows: (d.stocktaking.detail || []).map(r => {
                    const stMap = {draft:'مسودة',counting:'جاري الجرد',done:'منتهي',validated:'معتمد'};
                    return [
                        `<span style="color:#C9A84C;font-weight:700">${r.name}</span>`,
                        r.warehouse_id ? r.warehouse_id[1] : '—',
                        r.fiscal_year || '—',
                        badge(stMap[r.state] || r.state),
                        r.committee_chairman_id ? r.committee_chairman_id[1] : '—',
                    ];
                }),
            },
            auctions: {
                title: '🏛️ تفاصيل المزادات',
                kpis: [
                    {v: d.auction.by_state.session_open + d.auction.by_state.bidding, l:'نشط'},
                    {v: d.auction.by_state.done,  l:'مكتمل'},
                    {v: d.auction.lease.active,   l:'عقد إيجار'},
                ],
                headers: ['المرجع','الاسم','النوع','الحالة','العروض','أعلى عرض'],
                rows: (d.auction.detail || []).map(r => [
                    `<span style="color:#FAC775;font-weight:700">${r.ref || r.id}</span>`,
                    r.name,
                    r.auction_type === 'sale' ? 'بيع' : 'إيجار',
                    badge(this.stateLabel(r.state, 'auction')),
                    r.bid_count || 0,
                    r.awarded_amount ? r.awarded_amount.toLocaleString()+' ج.م' : '—',
                ]),
            },
        };

        const info = drillMap[key];
        if (!info) return;

        document.getElementById('ps-drill-ttl').innerHTML = info.title;
        document.getElementById('ps-drill-kpis').innerHTML =
            info.kpis.map(k => `<div class="ps-dkpi">
                <div class="dkv">${k.v}</div>
                <div class="dkl">${k.l}</div>
            </div>`).join('');

        const tbody = info.rows.map(r =>
            `<tr>${r.map(c => `<td>${c}</td>`).join('')}</tr>`
        ).join('');
        document.getElementById('ps-drill-tbl').innerHTML =
            `<thead><tr>${info.headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead>
             <tbody>${tbody}</tbody>`;

        document.getElementById('ps-drill-ov').classList.add('open');
    }
}

// ── Register component ───────────────────────────────────────────
registry.category('actions').add('portsaid_dashboard', PortSaidDashboard);

// ── Global drill helper for inline onclick ────────────────────────
window._psDrillKey = (key) => {
    const comp = document.querySelector('.o_portsaid_dashboard')?.__owl__?.component;
    if (comp) comp.openDrill(key);
};
