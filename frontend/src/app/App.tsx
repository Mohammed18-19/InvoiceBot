import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  LayoutDashboard, FileText, Settings, Plus, Bell,
  TrendingUp, AlertTriangle, CheckCircle2, Send, X,
  Upload, User, Palette, CreditCard, Trash2,
  Globe, Zap, ArrowLeft, Clock, Shield,
  MoreHorizontal, Eye, ChevronRight, Check,
} from "lucide-react";

// ─── TYPES ───────────────────────────────────────────────────────────
type Lang = "en" | "fr" | "ar";
type Page = "dashboard" | "detail" | "settings" | "invoices";
type Status = "pending" | "overdue" | "paid" | "draft";
type Currency = "MAD" | "EUR" | "USD";

interface Invoice {
  id: string;
  client: string;
  email: string;
  amount: number;
  currency: Currency;
  dueDate: string;
  status: Status;
  invoiceLang: Lang;
  remindersSent: number;
  createdAt: string;
}

// ─── TRANSLATIONS ─────────────────────────────────────────────────────
const T: Record<Lang, Record<string, string>> = {
  en: {
    appName: "InvoiceBot", planBadge: "Pro Plan",
    dashboard: "Dashboard", invoices: "Invoices", settings: "Settings",
    outstanding: "Outstanding", overdue: "Overdue", paidThisMonth: "Paid This Month",
    newInvoice: "New Invoice", sendReminder: "Send Reminder", markAsPaid: "Mark as Paid",
    clientName: "Client Name", amount: "Amount", dueDate: "Due Date",
    status: "Status", actions: "Actions",
    pending: "Pending", paid: "Paid", draft: "Draft", overdueLabel: "Overdue",
    welcomeBack: "Welcome back, Karim.", subtitle: "Here's what needs your attention today.",
    latestUnpaid: "Latest unpaid invoice", queuedInvoices: "invoices queued for reminders",
    createFirst: "Create your first invoice",
    createFirstDesc: "Start billing European clients and automate payment reminders in Arabic, French, or English.",
    createInvoice: "Create Invoice",
    saveActivate: "Save & Activate Reminders",
    reminderSchedule: "Reminder Schedule", livePreview: "Email Preview",
    currency: "Currency", langLabel: "Language", emailLabel: "Email Address",
    r3days: "3 days before due", rDue: "On due date", rAfter: "1 day after due", rCustom: "Custom",
    invoiceDetail: "Invoice Detail", reminderTimeline: "Reminder Timeline",
    activityLog: "Activity Log", scheduled: "Scheduled", sent: "Sent",
    invoiceNumber: "Invoice Number", recentInvoices: "Recent Invoices",
    profile: "Profile", branding: "Email Branding", notifications: "Notifications",
    planBilling: "Plan & Billing", dangerZone: "Danger Zone",
    currentPlan: "Current Plan", upgradePlan: "Upgrade Plan",
    deleteAccount: "Delete Account", fullName: "Full Name",
    uploadLogo: "Upload Logo", accentColor: "Email Accent Color",
    emailNotif: "Email Notifications", reminderNotif: "Reminder Alerts",
    backToDash: "Back to Dashboard", reminderSent: "Reminder sent",
    invoiceViewed: "Invoice viewed by client", activated: "Reminders activated",
    subjectLine: "Invoice {id} — Payment Due", greeting: "Dear {client},",
    emailBody: "This is a friendly reminder that invoice {id} for {amount} is due on {date}. Please process the payment at your earliest convenience.",
    emailFooter: "Thank you for your business.",
    reminders3d: "Reminder #1 sent", remindersOD: "Due date reminder", remindersAD: "Overdue notice",
  },
  fr: {
    appName: "InvoiceBot", planBadge: "Plan Pro",
    dashboard: "Tableau de bord", invoices: "Factures", settings: "Paramètres",
    outstanding: "En attente", overdue: "En retard", paidThisMonth: "Payé ce mois",
    newInvoice: "Nouvelle facture", sendReminder: "Envoyer rappel", markAsPaid: "Marquer payé",
    clientName: "Nom du client", amount: "Montant", dueDate: "Échéance",
    status: "Statut", actions: "Actions",
    pending: "En attente", paid: "Payé", draft: "Brouillon", overdueLabel: "En retard",
    welcomeBack: "Bon retour, Karim.", subtitle: "Voici ce qui mérite votre attention.",
    latestUnpaid: "Dernière facture impayée", queuedInvoices: "factures avec rappels actifs",
    createFirst: "Créez votre première facture",
    createFirstDesc: "Commencez à facturer vos clients et automatisez les relances en arabe, français ou anglais.",
    createInvoice: "Créer une facture",
    saveActivate: "Sauvegarder et activer les rappels",
    reminderSchedule: "Calendrier de rappel", livePreview: "Aperçu email",
    currency: "Devise", langLabel: "Langue", emailLabel: "Adresse email",
    r3days: "3 jours avant", rDue: "À l'échéance", rAfter: "1 jour après", rCustom: "Personnalisé",
    invoiceDetail: "Détail de la facture", reminderTimeline: "Rappels programmés",
    activityLog: "Journal d'activité", scheduled: "Planifié", sent: "Envoyé",
    invoiceNumber: "Numéro de facture", recentInvoices: "Factures récentes",
    profile: "Profil", branding: "Identité email", notifications: "Notifications",
    planBilling: "Plan et facturation", dangerZone: "Zone de danger",
    currentPlan: "Plan actuel", upgradePlan: "Mettre à niveau",
    deleteAccount: "Supprimer le compte", fullName: "Nom complet",
    uploadLogo: "Télécharger logo", accentColor: "Couleur accent email",
    emailNotif: "Notifications email", reminderNotif: "Alertes de rappel",
    backToDash: "Retour au tableau de bord", reminderSent: "Rappel envoyé",
    invoiceViewed: "Facture vue par le client", activated: "Rappels activés",
    subjectLine: "Facture {id} — Paiement dû", greeting: "Cher(e) {client},",
    emailBody: "Nous vous rappelons que la facture {id} d'un montant de {amount} est due le {date}. Merci de procéder au règlement dans les meilleurs délais.",
    emailFooter: "Merci pour votre confiance.",
    reminders3d: "Rappel n°1 envoyé", remindersOD: "Rappel à l'échéance", remindersAD: "Avis de retard",
  },
  ar: {
    appName: "إنفويس‌بوت", planBadge: "الباقة الاحترافية",
    dashboard: "لوحة التحكم", invoices: "الفواتير", settings: "الإعدادات",
    outstanding: "المعلقة", overdue: "متأخرة", paidThisMonth: "مدفوع هذا الشهر",
    newInvoice: "فاتورة جديدة", sendReminder: "إرسال تذكير", markAsPaid: "تحديد كمدفوع",
    clientName: "اسم العميل", amount: "المبلغ", dueDate: "تاريخ الاستحقاق",
    status: "الحالة", actions: "إجراءات",
    pending: "معلق", paid: "مدفوع", draft: "مسودة", overdueLabel: "متأخرة",
    welcomeBack: "مرحباً بعودتك، كريم.", subtitle: "إليك ما يحتاج انتباهك اليوم.",
    latestUnpaid: "آخر فاتورة غير مدفوعة", queuedInvoices: "فواتير في جدول التذكيرات",
    createFirst: "أنشئ فاتورتك الأولى",
    createFirstDesc: "ابدأ في إرسال الفواتير لعملائك وأتمتة تذكيرات الدفع بالعربية أو الفرنسية أو الإنجليزية.",
    createInvoice: "إنشاء فاتورة",
    saveActivate: "حفظ وتفعيل التذكيرات",
    reminderSchedule: "جدول التذكيرات", livePreview: "معاينة البريد",
    currency: "العملة", langLabel: "اللغة", emailLabel: "البريد الإلكتروني",
    r3days: "قبل 3 أيام", rDue: "في تاريخ الاستحقاق", rAfter: "بعد يوم واحد", rCustom: "مخصص",
    invoiceDetail: "تفاصيل الفاتورة", reminderTimeline: "جدول التذكيرات",
    activityLog: "سجل النشاط", scheduled: "مجدول", sent: "أُرسل",
    invoiceNumber: "رقم الفاتورة", recentInvoices: "الفواتير الأخيرة",
    profile: "الملف الشخصي", branding: "هوية البريد", notifications: "الإشعارات",
    planBilling: "الباقة والفوترة", dangerZone: "منطقة الخطر",
    currentPlan: "الباقة الحالية", upgradePlan: "ترقية الباقة",
    deleteAccount: "حذف الحساب", fullName: "الاسم الكامل",
    uploadLogo: "رفع الشعار", accentColor: "لون تمييز البريد",
    emailNotif: "إشعارات البريد", reminderNotif: "تنبيهات التذكير",
    backToDash: "العودة للوحة التحكم", reminderSent: "تم إرسال التذكير",
    invoiceViewed: "شاهد العميل الفاتورة", activated: "تم تفعيل التذكيرات",
    subjectLine: "فاتورة {id} — موعد الدفع", greeting: "عزيزي {client}،",
    emailBody: "نذكركم بأن الفاتورة رقم {id} بمبلغ {amount} تستحق بتاريخ {date}. يرجى المبادرة بالدفع في أقرب وقت ممكن.",
    emailFooter: "شكراً لتعاملكم معنا.",
    reminders3d: "التذكير الأول أُرسل", remindersOD: "تذكير تاريخ الاستحقاق", remindersAD: "إشعار التأخير",
  },
};

// ─── SAMPLE DATA ──────────────────────────────────────────────────────
const INVOICES: Invoice[] = [
  { id: "INV-2024-006", client: "Leblanc Studio", email: "finance@leblanc-studio.fr", amount: 2400, currency: "EUR", dueDate: "Jan 12, 2024", status: "overdue", invoiceLang: "fr", remindersSent: 2, createdAt: "Dec 28, 2023" },
  { id: "INV-2024-005", client: "TechFlow GmbH", email: "billing@techflow.de", amount: 1800, currency: "EUR", dueDate: "Jan 28, 2024", status: "pending", invoiceLang: "en", remindersSent: 0, createdAt: "Jan 5, 2024" },
  { id: "INV-2024-004", client: "Agence Numérique", email: "compta@agence-num.fr", amount: 3200, currency: "EUR", dueDate: "Feb 2, 2024", status: "pending", invoiceLang: "fr", remindersSent: 0, createdAt: "Jan 10, 2024" },
  { id: "INV-2024-003", client: "Studio Nord", email: "accounts@studionord.com", amount: 950, currency: "EUR", dueDate: "Jan 8, 2024", status: "paid", invoiceLang: "en", remindersSent: 1, createdAt: "Dec 22, 2023" },
  { id: "INV-2024-002", client: "Nexus Creative", email: "billing@nexus.io", amount: 1650, currency: "EUR", dueDate: "Jan 3, 2024", status: "paid", invoiceLang: "en", remindersSent: 2, createdAt: "Dec 15, 2023" },
];

// ─── HELPERS ──────────────────────────────────────────────────────────
function formatCurrency(amount: number, currency: Currency): string {
  const fmt = amount.toLocaleString("en-US");
  if (currency === "EUR") return `€${fmt}`;
  if (currency === "USD") return `$${fmt}`;
  return `${fmt} MAD`;
}

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia(query);
    setMatches(mq.matches);
    const h = (e: MediaQueryListEvent) => setMatches(e.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, [query]);
  return matches;
}

// ─── STATUS PILL ──────────────────────────────────────────────────────
function StatusPill({ status, t, small }: { status: Status; t: Record<string, string>; small?: boolean }) {
  const cfg: Record<Status, { bg: string; text: string; dot: string; label: string }> = {
    pending: { bg: "rgba(79,110,247,0.12)", text: "#4F6EF7", dot: "#4F6EF7", label: t.pending },
    overdue:  { bg: "rgba(247,201,79,0.12)",  text: "#F7C94F", dot: "#F7C94F", label: t.overdueLabel },
    paid:     { bg: "rgba(62,207,164,0.12)",  text: "#3ECFA4", dot: "#3ECFA4", label: t.paid },
    draft:    { bg: "rgba(122,130,153,0.12)", text: "#7A8299", dot: "#7A8299", label: t.draft },
  };
  const c = cfg[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full ${small ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1"}`}
      style={{ background: c.bg, color: c.text, transition: "background-color 150ms, color 150ms" }}
    >
      <span className="rounded-full" style={{ width: small ? 5 : 6, height: small ? 5 : 6, background: c.dot, flexShrink: 0 }} />
      {c.label}
    </span>
  );
}

// ─── METRIC CARD ──────────────────────────────────────────────────────
function MetricCard({
  label, value, sub, color, index, icon: Icon,
}: { label: string; value: string; sub?: string; color: string; index: number; icon: React.ElementType }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.07, ease: [0.22, 1, 0.36, 1] }}
      className="rounded-xl border border-[#1E2330] p-5 flex flex-col gap-3 group hover:border-[#2A3050] transition-colors"
      style={{ background: "#161A22", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider">{label}</span>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}18` }}>
          <Icon size={15} style={{ color }} />
        </div>
      </div>
      <div>
        <div className="text-3xl font-bold leading-none" style={{ fontFamily: '"Sora", sans-serif', color: "#F0F2F8" }}>
          {value}
        </div>
        {sub && <div className="text-xs text-[#7A8299] mt-1.5">{sub}</div>}
      </div>
    </motion.div>
  );
}

// ─── 3D INVOICE CARD ──────────────────────────────────────────────────
function InvoiceCard3D({ invoice, t }: { invoice: Invoice; t: Record<string, string> }) {
  const [tilt, setTilt] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const reducedMotion = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (reducedMotion || !containerRef.current) return;
    const r = containerRef.current.getBoundingClientRect();
    setTilt({
      x: ((e.clientY - r.top) / r.height - 0.5) * 10,
      y: ((e.clientX - r.left) / r.width - 0.5) * -16,
    });
  }, [reducedMotion]);

  const handleMouseLeave = useCallback(() => setTilt({ x: 0, y: 0 }), []);

  const cardStyle = (scale: number): React.CSSProperties => ({
    transform: `rotateX(${tilt.x * scale}deg) rotateY(${tilt.y * scale}deg)`,
    transition: "transform 200ms ease-out",
  });

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative mx-auto select-none"
      style={{ perspective: "1100px", width: 360, height: 220 }}
    >
      {/* Ambient glow */}
      <div
        className="absolute pointer-events-none"
        style={{
          inset: -40, background: "radial-gradient(ellipse 60% 50% at 50% 60%, rgba(79,110,247,0.10) 0%, transparent 70%)",
          filter: "blur(16px)", zIndex: 0,
        }}
      />
      {/* Ghost card 2 */}
      <div
        className="absolute inset-0 rounded-2xl border border-[#1E2330]"
        style={{ ...cardStyle(0.35), background: "#161A22", transform: `${cardStyle(0.35).transform} translate(14px, 22px)`, opacity: 0.22, zIndex: 1 }}
      />
      {/* Ghost card 1 */}
      <div
        className="absolute inset-0 rounded-2xl border border-[#222840]"
        style={{ ...cardStyle(0.65), background: "#1A1F2C", transform: `${cardStyle(0.65).transform} translate(7px, 11px)`, opacity: 0.55, zIndex: 2 }}
      />
      {/* Main card */}
      <div
        className="absolute inset-0 rounded-2xl border border-[#2A3060] p-5 overflow-hidden"
        style={{
          ...cardStyle(1),
          background: "linear-gradient(140deg, #1E2438 0%, #161A22 100%)",
          boxShadow: "0 24px 60px rgba(79,110,247,0.14), 0 8px 24px rgba(0,0,0,0.55)",
          zIndex: 3,
        }}
      >
        {/* Subtle radial highlight */}
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse 80% 60% at 80% 20%, rgba(79,110,247,0.07) 0%, transparent 60%)" }} />
        {/* Dot pattern watermark */}
        <div className="absolute bottom-3 right-4 opacity-[0.04] pointer-events-none" style={{ fontSize: 48, letterSpacing: "0.5em", color: "#4F6EF7" }}>⠿⠿⠿</div>

        <div className="relative z-10 flex flex-col h-full">
          <div className="flex justify-between items-start mb-4">
            <div>
              <div className="text-[10px] text-[#7A8299] uppercase tracking-[0.18em] font-medium mb-1">Invoice</div>
              <div className="text-sm font-semibold text-[#F0F2F8]">{invoice.id}</div>
            </div>
            <div className="flex items-center gap-1.5 rounded-full border border-[#4F6EF7]/25 px-2.5 py-1" style={{ background: "rgba(79,110,247,0.10)" }}>
              <Zap size={9} style={{ color: "#4F6EF7" }} />
              <span className="text-[9px] font-bold tracking-widest" style={{ color: "#4F6EF7" }}>INVOICEBOT</span>
            </div>
          </div>
          <div className="flex-1">
            <div className="text-[28px] font-bold leading-none text-[#F0F2F8] mb-1.5" style={{ fontFamily: '"Sora", sans-serif' }}>
              {formatCurrency(invoice.amount, invoice.currency)}
            </div>
            <div className="text-sm text-[#7A8299]">{invoice.client}</div>
          </div>
          <div className="flex justify-between items-center">
            <div className="text-[11px] text-[#7A8299]">Due {invoice.dueDate}</div>
            <StatusPill status={invoice.status} t={t} small />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── LANGUAGE TOGGLE ─────────────────────────────────────────────────
function LangToggle({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  const langs: { key: Lang; label: string }[] = [
    { key: "en", label: "EN" },
    { key: "fr", label: "FR" },
    { key: "ar", label: "AR" },
  ];
  return (
    <div className="flex items-center rounded-lg border border-[#1E2330] p-0.5 gap-0.5" style={{ background: "#111420" }}>
      {langs.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => setLang(key)}
          className="relative text-[11px] font-semibold tracking-wide px-2.5 py-1.5 rounded-md transition-colors"
          style={{ color: lang === key ? "#F0F2F8" : "#7A8299" }}
        >
          {lang === key && (
            <motion.span
              layoutId="lang-active"
              className="absolute inset-0 rounded-md"
              style={{ background: "#4F6EF7" }}
              transition={{ type: "spring", stiffness: 400, damping: 35 }}
            />
          )}
          <span className="relative z-10">{label}</span>
          {key === "ar" && <span className="relative z-10 ml-0.5 text-[8px] opacity-60">↔</span>}
        </button>
      ))}
    </div>
  );
}

// ─── TOP NAV ──────────────────────────────────────────────────────────
function TopNav({
  page, setPage, lang, setLang, t, onNewInvoice,
}: { page: Page; setPage: (p: Page) => void; lang: Lang; setLang: (l: Lang) => void; t: Record<string, string>; onNewInvoice: () => void }) {
  return (
    <header className="sticky top-0 z-40 border-b border-[#1E2330]" style={{ background: "rgba(13,15,20,0.92)", backdropFilter: "blur(12px)" }}>
      <div className="max-w-[1440px] mx-auto px-6 h-14 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg, #4F6EF7, #7B5FF7)" }}>
            <Zap size={14} className="text-white" />
          </div>
          <span className="text-[15px] font-semibold text-[#F0F2F8]" style={{ fontFamily: '"Sora", sans-serif' }}>
            InvoiceBot
          </span>
        </div>

        {/* Plan badge + nav (desktop) */}
        <div className="hidden md:flex items-center gap-6">
          <nav className="flex items-center gap-1">
            {([ ["dashboard", t.dashboard, LayoutDashboard], ["invoices", t.invoices, FileText], ["settings", t.settings, Settings] ] as [Page, string, React.ElementType][]).map(([key, label, Icon]) => (
              <button
                key={key}
                onClick={() => setPage(key)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                style={{ color: page === key ? "#F0F2F8" : "#7A8299", background: page === key ? "#1E2330" : "transparent" }}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </nav>
          <div className="h-4 w-px bg-[#1E2330]" />
          <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full border border-[#4F6EF7]/30" style={{ color: "#4F6EF7", background: "rgba(79,110,247,0.08)" }}>
            {t.planBadge}
          </span>
        </div>

        {/* Right: lang + bell + new invoice + avatar */}
        <div className="flex items-center gap-2.5 shrink-0">
          <LangToggle lang={lang} setLang={setLang} />
          <button className="w-8 h-8 rounded-lg flex items-center justify-center text-[#7A8299] hover:text-[#F0F2F8] hover:bg-[#1E2330] transition-colors relative">
            <Bell size={15} />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#F7C94F]" />
          </button>
          <button
            onClick={onNewInvoice}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-95"
            style={{ background: "linear-gradient(135deg, #4F6EF7 0%, #7B5FF7 100%)" }}
          >
            <Plus size={14} />
            {t.newInvoice}
          </button>
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold text-white shrink-0" style={{ background: "linear-gradient(135deg, #3ECFA4, #4F6EF7)" }}>
            K
          </div>
        </div>
      </div>
    </header>
  );
}

// ─── EMPTY STATE ──────────────────────────────────────────────────────
function EmptyState({ t, onCreateInvoice }: { t: Record<string, string>; onCreateInvoice: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <div className="w-20 h-20 rounded-2xl border border-[#1E2330] flex items-center justify-center mb-6" style={{ background: "#161A22" }}>
        <div className="relative">
          <FileText size={32} className="text-[#2A3050]" />
          <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-[#0D0F14] flex items-center justify-center" style={{ background: "#4F6EF7" }}>
            <Plus size={8} className="text-white" />
          </div>
        </div>
      </div>
      <h3 className="text-lg font-semibold text-[#F0F2F8] mb-2">{t.createFirst}</h3>
      <p className="text-sm text-[#7A8299] max-w-sm mb-6">{t.createFirstDesc}</p>
      <button
        onClick={onCreateInvoice}
        className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-95"
        style={{ background: "linear-gradient(135deg, #4F6EF7 0%, #7B5FF7 100%)" }}
      >
        <Plus size={15} />
        {t.createInvoice}
      </button>
    </div>
  );
}

// ─── INVOICE ROW ──────────────────────────────────────────────────────
function InvoiceRow({
  invoice, t, onSelect, onRemind, index,
}: { invoice: Invoice; t: Record<string, string>; onSelect: () => void; onRemind: () => void; index: number }) {
  const isOverdue = invoice.status === "overdue";
  return (
    <motion.tr
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="border-b border-[#1E2330] group cursor-pointer hover:bg-[#1A1F2C] transition-colors"
      onClick={onSelect}
    >
      <td className="py-3.5 pl-4 pr-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 text-[11px] font-bold"
            style={{ background: isOverdue ? "rgba(247,201,79,0.10)" : "rgba(79,110,247,0.10)", color: isOverdue ? "#F7C94F" : "#4F6EF7" }}>
            {invoice.client.charAt(0)}
          </div>
          <div>
            <div className="text-sm font-medium text-[#F0F2F8]">{invoice.client}</div>
            <div className="text-xs text-[#7A8299]">{invoice.email}</div>
          </div>
        </div>
      </td>
      <td className="py-3.5 px-3">
        <div className="text-sm font-semibold text-[#F0F2F8]" style={{ fontFamily: '"Sora", sans-serif' }}>
          {formatCurrency(invoice.amount, invoice.currency)}
        </div>
        <div className="text-[10px] text-[#7A8299]">{invoice.id}</div>
      </td>
      <td className="py-3.5 px-3 hidden sm:table-cell">
        <div className={`text-sm ${isOverdue ? "text-[#F7C94F]" : "text-[#7A8299]"}`}>{invoice.dueDate}</div>
      </td>
      <td className="py-3.5 px-3">
        <StatusPill status={invoice.status} t={t} />
      </td>
      <td className="py-3.5 pl-3 pr-4">
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {invoice.status !== "paid" && (
            <button
              onClick={(e) => { e.stopPropagation(); onRemind(); }}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all hover:opacity-90"
              style={{ background: "rgba(79,110,247,0.15)", color: "#4F6EF7" }}
            >
              <Send size={11} />
              <span className="hidden lg:inline">{t.sendReminder}</span>
            </button>
          )}
          <button className="w-7 h-7 rounded-lg flex items-center justify-center text-[#7A8299] hover:text-[#F0F2F8] hover:bg-[#1E2330] transition-colors">
            <Eye size={13} />
          </button>
        </div>
      </td>
    </motion.tr>
  );
}

// ─── CREATE INVOICE MODAL ────────────────────────────────────────────
function CreateInvoiceModal({ onClose, t, lang }: { onClose: () => void; t: Record<string, string>; lang: Lang }) {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const [form, setForm] = useState({ client: "", email: "", amount: "", currency: "EUR" as Currency, dueDate: "", invoiceLang: lang, schedule: "3days" });

  const update = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const previewLang = form.invoiceLang as Lang;
  const pt = T[previewLang];
  const previewAmount = form.amount ? formatCurrency(Number(form.amount), form.currency) : "€0.00";
  const emailBody = pt.emailBody
    .replace("{id}", "INV-2024-007")
    .replace("{amount}", previewAmount)
    .replace("{date}", form.dueDate || "—");

  return (
    <div className="fixed inset-0 z-50 flex items-end md:items-center justify-center">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/70"
        style={{ backdropFilter: "blur(4px)" }}
        onClick={onClose}
      />
      <motion.div
        initial={isMobile ? { y: "100%" } : { opacity: 0, scale: 0.96 }}
        animate={isMobile ? { y: 0 } : { opacity: 1, scale: 1 }}
        exit={isMobile ? { y: "100%" } : { opacity: 0, scale: 0.96 }}
        transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-10 w-full md:max-w-[820px] rounded-t-2xl md:rounded-2xl border border-[#1E2330] overflow-hidden flex flex-col md:flex-row"
        style={{ background: "#161A22", boxShadow: "0 24px 80px rgba(0,0,0,0.6)", maxHeight: "90vh" }}
      >
        {/* Left: Form */}
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-[#F0F2F8]">{t.createInvoice}</h2>
            <button onClick={onClose} className="w-8 h-8 rounded-lg flex items-center justify-center text-[#7A8299] hover:text-[#F0F2F8] hover:bg-[#1E2330] transition-colors">
              <X size={16} />
            </button>
          </div>

          <div className="space-y-4">
            {[
              { key: "client", label: t.clientName, type: "text", placeholder: "Leblanc Studio" },
              { key: "email", label: t.emailLabel, type: "email", placeholder: "finance@client.fr" },
            ].map(({ key, label, type, placeholder }) => (
              <label key={key} className="block">
                <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-1.5">{label}</span>
                <input
                  type={type}
                  placeholder={placeholder}
                  value={(form as Record<string, string>)[key]}
                  onChange={(e) => update(key, e.target.value)}
                  className="w-full rounded-lg border border-[#1E2330] px-3 py-2.5 text-sm text-[#F0F2F8] placeholder-[#3A4060] focus:outline-none focus:border-[#4F6EF7] transition-colors"
                  style={{ background: "#1A1F2C" }}
                />
              </label>
            ))}

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-1.5">{t.amount}</span>
                <input
                  type="number"
                  placeholder="2400"
                  value={form.amount}
                  onChange={(e) => update("amount", e.target.value)}
                  className="w-full rounded-lg border border-[#1E2330] px-3 py-2.5 text-sm text-[#F0F2F8] placeholder-[#3A4060] focus:outline-none focus:border-[#4F6EF7] transition-colors"
                  style={{ background: "#1A1F2C" }}
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-1.5">{t.currency}</span>
                <select
                  value={form.currency}
                  onChange={(e) => update("currency", e.target.value)}
                  className="w-full rounded-lg border border-[#1E2330] px-3 py-2.5 text-sm text-[#F0F2F8] focus:outline-none focus:border-[#4F6EF7] transition-colors"
                  style={{ background: "#1A1F2C" }}
                >
                  {["EUR", "USD", "MAD"].map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>
            </div>

            <label className="block">
              <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-1.5">{t.dueDate}</span>
              <input
                type="date"
                value={form.dueDate}
                onChange={(e) => update("dueDate", e.target.value)}
                className="w-full rounded-lg border border-[#1E2330] px-3 py-2.5 text-sm text-[#F0F2F8] focus:outline-none focus:border-[#4F6EF7] transition-colors"
                style={{ background: "#1A1F2C", colorScheme: "dark" }}
              />
            </label>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-1.5">{t.langLabel}</span>
                <select
                  value={form.invoiceLang}
                  onChange={(e) => update("invoiceLang", e.target.value)}
                  className="w-full rounded-lg border border-[#1E2330] px-3 py-2.5 text-sm text-[#F0F2F8] focus:outline-none focus:border-[#4F6EF7] transition-colors"
                  style={{ background: "#1A1F2C" }}
                >
                  <option value="en">English</option>
                  <option value="fr">Français</option>
                  <option value="ar">العربية</option>
                </select>
              </label>
              <label className="block">
                <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-1.5">{t.reminderSchedule}</span>
                <select
                  value={form.schedule}
                  onChange={(e) => update("schedule", e.target.value)}
                  className="w-full rounded-lg border border-[#1E2330] px-3 py-2.5 text-sm text-[#F0F2F8] focus:outline-none focus:border-[#4F6EF7] transition-colors"
                  style={{ background: "#1A1F2C" }}
                >
                  <option value="3days">{t.r3days}</option>
                  <option value="due">{t.rDue}</option>
                  <option value="after">{t.rAfter}</option>
                  <option value="custom">{t.rCustom}</option>
                </select>
              </label>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-full mt-6 py-3 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 active:scale-[0.99]"
            style={{ background: "linear-gradient(135deg, #4F6EF7 0%, #7B5FF7 100%)" }}
          >
            {t.saveActivate}
          </button>
        </div>

        {/* Right: Email preview */}
        <div className="hidden md:flex w-72 border-l border-[#1E2330] flex-col p-5 shrink-0" style={{ background: "#111420" }}>
          <div className="text-xs font-medium text-[#7A8299] uppercase tracking-wider mb-4 flex items-center gap-2">
            <Eye size={12} />
            {t.livePreview}
          </div>
          <div
            dir={previewLang === "ar" ? "rtl" : "ltr"}
            className="flex-1 rounded-xl border border-[#1E2330] p-4 text-xs overflow-y-auto"
            style={{ background: "#161A22", fontFamily: previewLang === "ar" ? '"IBM Plex Arabic", sans-serif' : '"Inter", sans-serif' }}
          >
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-[#1E2330]">
              <div className="w-6 h-6 rounded flex items-center justify-center" style={{ background: "linear-gradient(135deg, #4F6EF7, #7B5FF7)" }}>
                <Zap size={10} className="text-white" />
              </div>
              <span className="font-semibold text-[#F0F2F8] text-[10px] tracking-wide">INVOICEBOT</span>
            </div>
            <div className="text-[10px] text-[#7A8299] mb-1">{pt.subjectLine.replace("{id}", "INV-2024-007")}</div>
            <div className="text-xs font-medium text-[#F0F2F8] mb-3">{pt.greeting.replace("{client}", form.client || "Client")}</div>
            <div className="text-[11px] text-[#A0A8BF] leading-relaxed mb-4">{emailBody}</div>
            <div className="rounded-lg px-3 py-2 text-center text-[10px] font-semibold text-white mb-3" style={{ background: "#4F6EF7" }}>
              {previewLang === "ar" ? "عرض الفاتورة" : previewLang === "fr" ? "Voir la facture" : "View Invoice"}
            </div>
            <div className="text-[10px] text-[#7A8299] text-center border-t border-[#1E2330] pt-3">{pt.emailFooter}</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

// ─── DASHBOARD ────────────────────────────────────────────────────────
function Dashboard({
  invoices, t, lang, onSelect, onCreateInvoice,
}: { invoices: Invoice[]; t: Record<string, string>; lang: Lang; onSelect: (inv: Invoice) => void; onCreateInvoice: () => void }) {
  const outstanding = invoices.filter((i) => i.status !== "paid").reduce((s, i) => s + i.amount, 0);
  const overdueCount = invoices.filter((i) => i.status === "overdue").length;
  const paidSum = invoices.filter((i) => i.status === "paid").reduce((s, i) => s + i.amount, 0);
  const latestUnpaid = invoices.find((i) => i.status !== "paid");
  const [remindSent, setRemindSent] = useState<string | null>(null);

  const sendRemind = (id: string) => {
    setRemindSent(id);
    setTimeout(() => setRemindSent(null), 2000);
  };

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div>
        <h1 className="text-xl font-semibold text-[#F0F2F8]">{t.welcomeBack}</h1>
        <p className="text-sm text-[#7A8299] mt-0.5">{t.subtitle}</p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard label={t.outstanding} value={`€${outstanding.toLocaleString()}`} sub="across 3 active invoices" color="#4F6EF7" index={0} icon={TrendingUp} />
        <MetricCard label={t.overdue} value={String(overdueCount)} sub="invoices past due date" color="#F7C94F" index={1} icon={AlertTriangle} />
        <MetricCard label={t.paidThisMonth} value={`€${paidSum.toLocaleString()}`} sub="2 invoices settled" color="#3ECFA4" index={2} icon={CheckCircle2} />
      </div>

      {/* 3D Hero */}
      {latestUnpaid ? (
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
          className="rounded-2xl border border-[#1E2330] p-8 flex flex-col md:flex-row items-center gap-8"
          style={{ background: "#161A22", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}
        >
          <div className="flex-1 md:max-w-xs">
            <div className="text-[10px] text-[#4F6EF7] font-semibold uppercase tracking-widest mb-2">{t.latestUnpaid}</div>
            <h2 className="text-2xl font-bold text-[#F0F2F8] mb-1" style={{ fontFamily: '"Sora", sans-serif' }}>
              {formatCurrency(latestUnpaid.amount, latestUnpaid.currency)}
            </h2>
            <p className="text-sm text-[#7A8299] mb-4">{latestUnpaid.client} · {latestUnpaid.dueDate}</p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => onSelect(latestUnpaid)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90"
                style={{ background: "linear-gradient(135deg, #4F6EF7 0%, #7B5FF7 100%)" }}
              >
                <Eye size={13} />
                View Invoice
              </button>
              <button
                onClick={() => sendRemind(latestUnpaid.id)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border border-[#1E2330] transition-all hover:border-[#4F6EF7]/40 hover:text-[#F0F2F8]"
                style={{ color: "#7A8299", background: "transparent" }}
              >
                {remindSent === latestUnpaid.id ? <><Check size={13} style={{ color: "#3ECFA4" }} /> Sent!</> : <><Send size={13} /> {t.sendReminder}</>}
              </button>
            </div>
            <div className="mt-4 text-xs text-[#7A8299]">
              <span className="text-[#4F6EF7] font-medium">{invoices.filter((i) => i.status !== "paid").length}</span> {t.queuedInvoices}
            </div>
          </div>
          <div className="flex-1 flex justify-center py-4 md:py-0">
            <InvoiceCard3D invoice={latestUnpaid} t={t} />
          </div>
        </motion.div>
      ) : null}

      {/* Invoice table */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-[#F0F2F8]">{t.recentInvoices}</h2>
          <button
            onClick={onCreateInvoice}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white sm:hidden transition-all hover:opacity-90"
            style={{ background: "linear-gradient(135deg, #4F6EF7, #7B5FF7)" }}
          >
            <Plus size={12} />
            {t.newInvoice}
          </button>
        </div>
        <div className="rounded-xl border border-[#1E2330] overflow-hidden" style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
          {invoices.length === 0 ? (
            <EmptyState t={t} onCreateInvoice={onCreateInvoice} />
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#1E2330]" style={{ background: "#111420" }}>
                  {[t.clientName, t.amount, t.dueDate, t.status, t.actions].map((h, i) => (
                    <th key={i} className={`text-left text-[10px] font-semibold text-[#7A8299] uppercase tracking-wider py-3 ${i === 0 ? "pl-4 pr-3" : i === 4 ? "pl-3 pr-4" : "px-3"} ${i === 2 ? "hidden sm:table-cell" : ""}`}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv, i) => (
                  <InvoiceRow
                    key={inv.id}
                    invoice={inv}
                    t={t}
                    onSelect={() => onSelect(inv)}
                    onRemind={() => sendRemind(inv.id)}
                    index={i}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── INVOICE DETAIL ───────────────────────────────────────────────────
function InvoiceDetailPage({
  invoice, t, onBack,
}: { invoice: Invoice; t: Record<string, string>; onBack: () => void }) {
  const [isPaid, setIsPaid] = useState(invoice.status === "paid");

  const timeline = [
    { label: t.reminders3d, date: "Jan 9, 2024 · 09:00", done: true },
    { label: t.remindersOD, date: "Jan 12, 2024 · 09:00", done: invoice.status !== "pending" },
    { label: t.remindersAD, date: "Jan 13, 2024 · 09:00", done: false },
  ];

  const activity = [
    { text: t.activated, time: "Dec 28, 2023 · 14:30", icon: Zap, color: "#4F6EF7" },
    { text: t.reminderSent + " #1", time: "Jan 9, 2024 · 09:01", icon: Send, color: "#3ECFA4" },
    { text: t.reminderSent + " #2", time: "Jan 12, 2024 · 09:00", icon: Send, color: "#3ECFA4" },
    { text: t.invoiceViewed, time: "Jan 12, 2024 · 11:47", icon: Eye, color: "#7A8299" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="space-y-6"
    >
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-sm text-[#7A8299] hover:text-[#F0F2F8] transition-colors"
      >
        <ArrowLeft size={14} />
        {t.backToDash}
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Invoice info */}
        <div className="lg:col-span-2 space-y-5">
          <div className="rounded-xl border border-[#1E2330] p-6" style={{ background: "#161A22", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
            <div className="flex items-start justify-between mb-6">
              <div>
                <div className="text-[10px] text-[#7A8299] uppercase tracking-widest mb-1">{t.invoiceNumber}</div>
                <div className="text-2xl font-bold text-[#F0F2F8]" style={{ fontFamily: '"Sora", sans-serif' }}>{invoice.id}</div>
              </div>
              <StatusPill status={isPaid ? "paid" : invoice.status} t={t} />
            </div>
            <div className="grid grid-cols-2 gap-6 mb-6">
              {[
                { label: t.clientName, value: invoice.client },
                { label: t.emailLabel, value: invoice.email },
                { label: t.amount, value: formatCurrency(invoice.amount, invoice.currency) },
                { label: t.dueDate, value: invoice.dueDate },
              ].map(({ label, value }) => (
                <div key={label}>
                  <div className="text-[10px] text-[#7A8299] uppercase tracking-wider mb-1">{label}</div>
                  <div className="text-sm font-medium text-[#F0F2F8]">{value}</div>
                </div>
              ))}
            </div>
            {!isPaid && (
              <button
                onClick={() => setIsPaid(true)}
                className="w-full py-3 rounded-xl text-sm font-bold transition-all hover:opacity-90 active:scale-[0.99]"
                style={{ background: "#F7C94F", color: "#0D0F14" }}
              >
                <span className="flex items-center justify-center gap-2">
                  <CheckCircle2 size={16} />
                  {t.markAsPaid}
                </span>
              </button>
            )}
            {isPaid && (
              <div className="w-full py-3 rounded-xl text-sm font-bold text-center flex items-center justify-center gap-2" style={{ background: "rgba(62,207,164,0.12)", color: "#3ECFA4" }}>
                <CheckCircle2 size={16} />
                {t.paid}
              </div>
            )}
          </div>

          {/* Activity log */}
          <div className="rounded-xl border border-[#1E2330] p-5" style={{ background: "#161A22", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
            <h3 className="text-sm font-semibold text-[#F0F2F8] mb-4">{t.activityLog}</h3>
            <div className="space-y-3">
              {activity.map(({ text, time, icon: Icon, color }, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5" style={{ background: `${color}14` }}>
                    <Icon size={12} style={{ color }} />
                  </div>
                  <div>
                    <div className="text-sm text-[#F0F2F8]">{text}</div>
                    <div className="text-[11px] text-[#7A8299]">{time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Reminder timeline */}
        <div className="rounded-xl border border-[#1E2330] p-5 h-fit" style={{ background: "#161A22", boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
          <h3 className="text-sm font-semibold text-[#F0F2F8] mb-5">{t.reminderTimeline}</h3>
          <div className="relative">
            <div className="absolute left-3 top-3 bottom-3 w-px bg-[#1E2330]" />
            <div className="space-y-6">
              {timeline.map(({ label, date, done }, i) => (
                <div key={i} className="flex gap-4 items-start">
                  <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 z-10 transition-all`}
                    style={{ background: done ? "#3ECFA4" : "#1E2330", borderColor: done ? "#3ECFA4" : "#2A3050" }}>
                    {done && <Check size={10} className="text-[#0D0F14]" />}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-[#F0F2F8]">{label}</div>
                    <div className="text-[11px] text-[#7A8299] mt-0.5">{date}</div>
                    <span className={`inline-block mt-1.5 text-[10px] font-medium px-2 py-0.5 rounded-full`}
                      style={{ background: done ? "rgba(62,207,164,0.10)" : "rgba(79,110,247,0.10)", color: done ? "#3ECFA4" : "#4F6EF7" }}>
                      {done ? t.sent : t.scheduled}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// ─── SETTINGS ─────────────────────────────────────────────────────────
function SettingsPage({ t }: { t: Record<string, string> }) {
  const [accentColor, setAccentColor] = useState("#4F6EF7");
  const [notifs, setNotifs] = useState({ email: true, reminders: true });
  const colors = ["#4F6EF7", "#3ECFA4", "#F7C94F", "#E85D5D", "#9B7EF7", "#F77A4F"];

  const Section = ({ title, icon: Icon, children }: { title: string; icon: React.ElementType; children: React.ReactNode }) => (
    <div className="rounded-xl border border-[#1E2330] overflow-hidden" style={{ boxShadow: "0 4px 24px rgba(0,0,0,0.4)" }}>
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-[#1E2330]" style={{ background: "#111420" }}>
        <Icon size={14} className="text-[#7A8299]" />
        <h3 className="text-sm font-semibold text-[#F0F2F8]">{title}</h3>
      </div>
      <div className="p-5 space-y-4" style={{ background: "#161A22" }}>
        {children}
      </div>
    </div>
  );

  const Field = ({ label, defaultVal, type = "text" }: { label: string; defaultVal: string; type?: string }) => (
    <label className="block">
      <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-1.5">{label}</span>
      <input
        type={type}
        defaultValue={defaultVal}
        className="w-full rounded-lg border border-[#1E2330] px-3 py-2.5 text-sm text-[#F0F2F8] focus:outline-none focus:border-[#4F6EF7] transition-colors"
        style={{ background: "#1A1F2C" }}
      />
    </label>
  );

  const Toggle = ({ label, checked, onChange }: { label: string; checked: boolean; onChange: () => void }) => (
    <div className="flex items-center justify-between">
      <span className="text-sm text-[#F0F2F8]">{label}</span>
      <button
        onClick={onChange}
        className="w-10 h-5.5 rounded-full relative transition-colors"
        style={{ background: checked ? "#4F6EF7" : "#1E2330", height: 22, width: 42 }}
      >
        <span className="absolute top-0.5 rounded-full bg-white transition-all" style={{ left: checked ? "calc(100% - 20px)" : 2, width: 18, height: 18 }} />
      </button>
    </div>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="max-w-2xl space-y-5"
    >
      <h1 className="text-xl font-semibold text-[#F0F2F8]">{t.settings}</h1>

      <Section title={t.profile} icon={User}>
        <Field label={t.fullName} defaultVal="Karim Benali" />
        <Field label={t.emailLabel} defaultVal="karim@freelance.ma" type="email" />
      </Section>

      <Section title={t.branding} icon={Palette}>
        <div>
          <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-3">{t.uploadLogo}</span>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl border-2 border-dashed border-[#2A3050] flex items-center justify-center hover:border-[#4F6EF7] transition-colors cursor-pointer">
              <Upload size={16} className="text-[#7A8299]" />
            </div>
            <div className="text-xs text-[#7A8299]">PNG, SVG · max 1MB</div>
          </div>
        </div>
        <div>
          <span className="text-xs font-medium text-[#7A8299] uppercase tracking-wider block mb-3">{t.accentColor}</span>
          <div className="flex items-center gap-2">
            {colors.map((c) => (
              <button
                key={c}
                onClick={() => setAccentColor(c)}
                className="w-7 h-7 rounded-lg transition-all hover:scale-110"
                style={{
                  background: c,
                  outline: accentColor === c ? `2px solid ${c}` : "none",
                  outlineOffset: 2,
                  boxShadow: accentColor === c ? `0 0 12px ${c}40` : "none",
                }}
              />
            ))}
          </div>
        </div>
      </Section>

      <Section title={t.notifications} icon={Bell}>
        <Toggle label={t.emailNotif} checked={notifs.email} onChange={() => setNotifs((n) => ({ ...n, email: !n.email }))} />
        <div className="h-px bg-[#1E2330]" />
        <Toggle label={t.reminderNotif} checked={notifs.reminders} onChange={() => setNotifs((n) => ({ ...n, reminders: !n.reminders }))} />
      </Section>

      <Section title={t.planBilling} icon={CreditCard}>
        <div className="flex items-center justify-between p-4 rounded-xl border border-[#4F6EF7]/20" style={{ background: "rgba(79,110,247,0.06)" }}>
          <div>
            <div className="text-sm font-semibold text-[#F0F2F8]">{t.currentPlan}</div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: "rgba(79,110,247,0.15)", color: "#4F6EF7" }}>Pro</span>
              <span className="text-xs text-[#7A8299]">$20 / month · Unlimited invoices</span>
            </div>
          </div>
          <ChevronRight size={16} className="text-[#7A8299]" />
        </div>
        <button className="w-full py-2.5 rounded-lg border border-[#1E2330] text-sm font-medium text-[#7A8299] hover:text-[#F0F2F8] hover:border-[#2A3050] transition-colors">
          Manage billing →
        </button>
      </Section>

      <Section title={t.dangerZone} icon={Shield}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-medium text-[#F0F2F8]">{t.deleteAccount}</div>
            <div className="text-xs text-[#7A8299] mt-0.5">This action is irreversible. All data will be deleted.</div>
          </div>
          <button className="px-4 py-2 rounded-lg border border-[#E85D5D]/30 text-xs font-semibold transition-all hover:bg-[#E85D5D]/10" style={{ color: "#E85D5D" }}>
            <Trash2 size={13} className="inline mr-1.5" />
            {t.deleteAccount}
          </button>
        </div>
      </Section>
    </motion.div>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────
export default function App() {
  const [lang, setLang] = useState<Lang>("en");
  const [page, setPage] = useState<Page>("dashboard");
  const [showModal, setShowModal] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  const t = T[lang];
  const isRTL = lang === "ar";

  const handleSelect = (inv: Invoice) => {
    setSelectedInvoice(inv);
    setPage("detail");
  };

  const handleSetPage = (p: Page) => {
    setPage(p);
    if (p !== "detail") setSelectedInvoice(null);
  };

  return (
    <div
      dir={isRTL ? "rtl" : "ltr"}
      className="min-h-screen bg-background text-foreground"
      style={{ fontFamily: isRTL ? '"IBM Plex Arabic", "Inter", sans-serif' : '"Inter", sans-serif' }}
    >
      <TopNav
        page={page}
        setPage={handleSetPage}
        lang={lang}
        setLang={setLang}
        t={t}
        onNewInvoice={() => setShowModal(true)}
      />

      <main className="max-w-[1440px] mx-auto px-4 sm:px-6 py-8 pb-24 md:pb-10">
        {page === "dashboard" && (
          <Dashboard
            invoices={INVOICES}
            t={t}
            lang={lang}
            onSelect={handleSelect}
            onCreateInvoice={() => setShowModal(true)}
          />
        )}
        {page === "detail" && selectedInvoice && (
          <InvoiceDetailPage
            invoice={selectedInvoice}
            t={t}
            onBack={() => handleSetPage("dashboard")}
          />
        )}
        {page === "settings" && <SettingsPage t={t} />}
        {page === "invoices" && (
          <Dashboard
            invoices={INVOICES}
            t={t}
            lang={lang}
            onSelect={handleSelect}
            onCreateInvoice={() => setShowModal(true)}
          />
        )}
      </main>

      {/* Mobile bottom nav */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 border-t border-[#1E2330] flex"
        style={{ background: "rgba(22,26,34,0.97)", backdropFilter: "blur(12px)" }}
      >
        {([
          ["dashboard", t.dashboard, LayoutDashboard],
          ["invoices", t.invoices, FileText],
          ["settings", t.settings, Settings],
        ] as [Page, string, React.ElementType][]).map(([key, label, Icon]) => (
          <button
            key={key}
            onClick={() => handleSetPage(key)}
            className="flex-1 flex flex-col items-center gap-1 py-3 transition-colors"
            style={{ color: page === key ? "#4F6EF7" : "#7A8299" }}
          >
            <Icon size={20} />
            <span className="text-[10px] font-medium">{label}</span>
          </button>
        ))}
      </nav>

      <AnimatePresence>
        {showModal && (
          <CreateInvoiceModal
            onClose={() => setShowModal(false)}
            t={t}
            lang={lang}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
