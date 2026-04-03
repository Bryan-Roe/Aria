(function () {
    "use strict";

    if (window.__ariaSiteUpgradeLoaded) {
        return;
    }
    window.__ariaSiteUpgradeLoaded = true;

    document.documentElement.classList.add("site-upgraded");

    var PASS_MIN = 1;
    var PASS_MAX = 100;
    var PASS_DEFAULT = 100;
    var PASS_STORAGE_KEY = "siteUpgradePasses";
    var DEBUG_OPEN_STORAGE_KEY = "siteUpgradePassDebugOpen";
    var PASS_AUTOPLAY_INTERVAL_MS = 70;
    var PASS_AUTOPLAY_MIN_MS = 25;
    var PASS_AUTOPLAY_MAX_MS = 1000;
    var PASS_AUTOPLAY_STORAGE_KEY = "siteUpgradePassSweepMs";
    var PASS_SNAPSHOT_STORAGE_KEY = "siteUpgradePassSnapshots";
    var PASS_UNDO_STORAGE_KEY = "siteUpgradePassUndoStack";
    var PASS_SECTIONS_STORAGE_KEY = "siteUpgradePassSections";
    var PASS_POSITION_STORAGE_KEY = "siteUpgradePassPosition";
    var PASS_WIDTH_STORAGE_KEY = "siteUpgradePassWidth";
    var PASS_PANEL_STYLE_STORAGE_KEY = "siteUpgradePassPanelStyle";
    var PASS_HISTORY_MAX = 10;

    function detectSiteKind() {
        var path = (window.location.pathname || "").toLowerCase();
        var href = (window.location.href || "").toLowerCase();
        var target = path + " " + href;

        if (target.includes("/chat/") || target.includes("chat/index") || target.endsWith("/chat")) {
            return "chat";
        }

        if (target.includes("/aria/") || target.includes("auto-execute") || target.includes("aria/index")) {
            return "aria";
        }

        if (target.includes("/dashboard/") || target.includes("dashboard/index") || target.includes("dashboard/hub")) {
            return "dashboard";
        }

        if (target.includes("/store/") || target.includes("products") || target.includes("product.html")) {
            return "store";
        }

        if (target.includes("documentation") || target.includes("/docs/") || target.endsWith("/docs") || target.includes("readme_pages")) {
            return "docs";
        }

        if (target.includes("/quantum/") || target.includes("/monetization/") || target.includes("llm-maker") || target.includes("/mount/")) {
            return "dashboard";
        }

        return "core";
    }

    function applySiteKindClass() {
        var kind = detectSiteKind();
        var root = document.documentElement;
        var body = document.body;

        root.setAttribute("data-site-kind", kind);
        if (body) {
            body.setAttribute("data-site-kind", kind);
            body.classList.add("site-kind-" + kind);
        }

        return kind;
    }

    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function getPassStorageKey(kind) {
        return PASS_STORAGE_KEY + ":" + kind;
    }

    function getPassSpeedStorageKey(kind) {
        return PASS_AUTOPLAY_STORAGE_KEY + ":" + kind;
    }

    function getPassSnapshotStorageKey(kind) {
        return PASS_SNAPSHOT_STORAGE_KEY + ":" + kind;
    }

    function getPassUndoStorageKey(kind) {
        return PASS_UNDO_STORAGE_KEY + ":" + kind;
    }

    function getPassSectionsStorageKey(kind) {
        return PASS_SECTIONS_STORAGE_KEY + ":" + kind;
    }

    function getPassPositionStorageKey(kind) {
        return PASS_POSITION_STORAGE_KEY + ":" + kind;
    }

    function getPassWidthStorageKey(kind) {
        return PASS_WIDTH_STORAGE_KEY + ":" + kind;
    }

    function getPassPanelStyleStorageKey(kind) {
        return PASS_PANEL_STYLE_STORAGE_KEY + ":" + kind;
    }

    function shouldOpenDebugFromQuery() {
        var params = new URLSearchParams(window.location.search || "");
        var raw = params.get("passpanel") || params.get("debugpasses") || params.get("passdebug");
        if (!raw) {
            return null;
        }

        var value = String(raw).toLowerCase();
        if (value === "0" || value === "false" || value === "off" || value === "hide") {
            return false;
        }

        return true;
    }

    function shouldAutoplayFromQuery() {
        var params = new URLSearchParams(window.location.search || "");
        var raw = params.get("passauto") || params.get("passautoplay") || params.get("autosweep");
        if (!raw) {
            return null;
        }

        return toOptionalBool(raw);
    }

    function getConfiguredPassCount(kind) {
        var params = new URLSearchParams(window.location.search || "");
        var stateFromQuery = getPassStateFromQuery();
        var queryRaw = params.get("passes") || params.get("pass") || (stateFromQuery && stateFromQuery.passCount);
        var savedRaw = null;

        try {
            if (window.localStorage) {
                savedRaw = localStorage.getItem(getPassStorageKey(kind)) || localStorage.getItem(PASS_STORAGE_KEY);
            }
        } catch (error) {
            savedRaw = null;
        }

        var parsed = Number(queryRaw || savedRaw || PASS_DEFAULT);
        if (!Number.isFinite(parsed)) {
            parsed = PASS_DEFAULT;
        }

        return Math.round(clamp(parsed, PASS_MIN, PASS_MAX));
    }

    function getConfiguredAutoplayInterval(kind) {
        var params = new URLSearchParams(window.location.search || "");
        var stateFromQuery = getPassStateFromQuery();
        var queryRaw = params.get("passsweepms") || params.get("passautoplayms") || params.get("passspeed") || (stateFromQuery && stateFromQuery.sweepMs);
        var savedRaw = null;

        try {
            if (window.localStorage) {
                savedRaw = localStorage.getItem(getPassSpeedStorageKey(kind)) || localStorage.getItem(PASS_AUTOPLAY_STORAGE_KEY);
            }
        } catch (error) {
            savedRaw = null;
        }

        var parsed = Number(queryRaw || savedRaw || PASS_AUTOPLAY_INTERVAL_MS);
        if (!Number.isFinite(parsed)) {
            parsed = PASS_AUTOPLAY_INTERVAL_MS;
        }

        return Math.round(clamp(parsed, PASS_AUTOPLAY_MIN_MS, PASS_AUTOPLAY_MAX_MS));
    }

    function normalizePassSource(source) {
        var normalized = String(source || "manual");

        if (normalized.indexOf("shortcut-") === 0) {
            normalized = "key " + normalized.slice("shortcut-".length);
        }

        return normalized.replace(/-/g, " ");
    }

    function toValidPass(rawValue) {
        var parsed = Number(rawValue);
        if (!Number.isFinite(parsed)) {
            return null;
        }

        return Math.round(clamp(parsed, PASS_MIN, PASS_MAX));
    }

    function toValidSpeed(rawValue) {
        var parsed = Number(rawValue);
        if (!Number.isFinite(parsed)) {
            return null;
        }

        return Math.round(clamp(parsed, PASS_AUTOPLAY_MIN_MS, PASS_AUTOPLAY_MAX_MS));
    }

    function toOptionalBool(rawValue) {
        if (typeof rawValue === "boolean") {
            return rawValue;
        }

        if (rawValue === null || rawValue === undefined) {
            return null;
        }

        var normalized = String(rawValue).toLowerCase();
        if (normalized === "1" || normalized === "true" || normalized === "on" || normalized === "open" || normalized === "yes") {
            return true;
        }

        if (normalized === "0" || normalized === "false" || normalized === "off" || normalized === "close" || normalized === "closed" || normalized === "hide" || normalized === "no") {
            return false;
        }

        return null;
    }

    function normalizePassState(rawState) {
        if (!rawState || typeof rawState !== "object") {
            return null;
        }

        var passCount = toValidPass(rawState.passCount !== undefined ? rawState.passCount : (rawState.pass !== undefined ? rawState.pass : rawState.p));
        var sweepMs = toValidSpeed(rawState.sweepMs !== undefined ? rawState.sweepMs : (rawState.speed !== undefined ? rawState.speed : rawState.ms));
        var snapshotA = toValidPass(rawState.snapshotA !== undefined ? rawState.snapshotA : rawState.a);
        var snapshotB = toValidPass(rawState.snapshotB !== undefined ? rawState.snapshotB : rawState.b);
        var open = toOptionalBool(rawState.open);
        var auto = toOptionalBool(rawState.auto);

        if (passCount === null && sweepMs === null && snapshotA === null && snapshotB === null && open === null && auto === null) {
            return null;
        }

        return {
            passCount: passCount,
            sweepMs: sweepMs,
            snapshotA: snapshotA,
            snapshotB: snapshotB,
            open: open,
            auto: auto
        };
    }

    function getPassStateFromSearchParams(params) {
        if (!params) {
            return null;
        }

        var raw = params.get("passstate");
        if (!raw) {
            return null;
        }

        try {
            return normalizePassState(JSON.parse(raw));
        } catch (error) {
            return null;
        }
    }

    function getPassStateFromQuery() {
        return getPassStateFromSearchParams(new URLSearchParams(window.location.search || ""));
    }

    function parsePassStateFromInput(rawInput) {
        if (!rawInput) {
            return null;
        }

        var value = String(rawInput).trim();
        if (!value) {
            return null;
        }

        try {
            var url = new URL(value, window.location.href);
            var fromUrl = getPassStateFromSearchParams(url.searchParams);
            if (fromUrl) {
                return fromUrl;
            }
        } catch (error) {
            // Not a URL, continue parsing.
        }

        try {
            var queryLike = value.charAt(0) === "?" ? value.slice(1) : value;
            var params = new URLSearchParams(queryLike);
            var fromParams = getPassStateFromSearchParams(params);
            if (fromParams) {
                return fromParams;
            }
        } catch (error) {
            // Not query-like content, continue parsing.
        }

        try {
            return normalizePassState(JSON.parse(value));
        } catch (error) {
            return null;
        }
    }

    function interpolate(start, end, t) {
        return start + (end - start) * t;
    }

    function getKindShadowColor(kind) {
        switch (kind) {
            case "chat":
                return [15, 147, 197];
            case "aria":
                return [46, 157, 131];
            case "dashboard":
                return [47, 123, 231];
            case "store":
                return [208, 96, 47];
            case "docs":
                return [24, 127, 120];
            default:
                return [19, 36, 55];
        }
    }

    function setPassVariables(kind, passIndex, totalPasses) {
        var root = document.documentElement;
        var t = clamp(passIndex / totalPasses, 0, 1);
        var color = getKindShadowColor(kind);

        var gridOpacity = interpolate(0.24, 0.46, t);
        var radiusBoost = interpolate(0, 7, t);
        var focusWidth = interpolate(2.5, 4.2, t);
        var letterShift = interpolate(-0.012, -0.036, t);
        var cardRaise = interpolate(0.25, 1.9, t);
        var revealMs = Math.round(interpolate(430, 690, t));

        var softY = interpolate(8, 24, t);
        var softBlur = interpolate(22, 54, t);
        var softAlpha = interpolate(0.14, 0.33, t);

        var strongY = interpolate(14, 38, t);
        var strongBlur = interpolate(34, 78, t);
        var strongAlpha = interpolate(0.2, 0.42, t);

        root.style.setProperty("--pass-intensity", t.toFixed(4));
        root.style.setProperty("--pass-grid-opacity", gridOpacity.toFixed(3));
        root.style.setProperty("--pass-radius-boost", radiusBoost.toFixed(2) + "px");
        root.style.setProperty("--pass-focus-width", focusWidth.toFixed(2) + "px");
        root.style.setProperty("--pass-letter-shift", letterShift.toFixed(4) + "em");
        root.style.setProperty("--pass-card-raise", cardRaise.toFixed(2) + "px");
        root.style.setProperty("--pass-reveal-ms", revealMs + "ms");
        root.style.setProperty(
            "--pass-shadow-soft",
            "0 " + softY.toFixed(2) + "px " + softBlur.toFixed(2) + "px rgba(" + color[0] + ", " + color[1] + ", " + color[2] + ", " + softAlpha.toFixed(3) + ")"
        );
        root.style.setProperty(
            "--pass-shadow-strong",
            "0 " + strongY.toFixed(2) + "px " + strongBlur.toFixed(2) + "px rgba(" + color[0] + ", " + color[1] + ", " + color[2] + ", " + strongAlpha.toFixed(3) + ")"
        );
    }

    function emitPassChange(kind, passCount, source) {
        var detail = {
            kind: kind,
            passCount: passCount,
            passes: passCount,
            source: source || "manual"
        };

        document.dispatchEvent(new CustomEvent("site-upgrade:pass-change", { detail: detail }));
        window.dispatchEvent(new CustomEvent("site-upgrade:pass-change", { detail: detail }));
    }

    function runPolishPasses(kind, requestedPassCount, source) {
        var passCount = Math.round(clamp(Number(requestedPassCount), PASS_MIN, PASS_MAX));

        for (var pass = 1; pass <= passCount; pass += 1) {
            setPassVariables(kind, pass, passCount);
        }

        document.documentElement.setAttribute("data-polish-passes", String(passCount));
        if (document.body) {
            document.body.setAttribute("data-polish-passes", String(passCount));
        }

        emitPassChange(kind, passCount, source);

        return passCount;
    }

    function trySaveValue(key, value) {
        try {
            if (window.localStorage) {
                localStorage.setItem(key, value);
            }
        } catch (error) {
            // Ignore storage errors in strict/private browsing contexts.
        }
    }

    function tryLoadValue(key) {
        try {
            return window.localStorage ? localStorage.getItem(key) : null;
        } catch (error) {
            return null;
        }
    }

    function createPassDebugPanel(kind, initialPassCount) {
        if (!document.body || document.querySelector(".site-pass-debug")) {
            return;
        }

        var panel = document.createElement("aside");
        panel.className = "site-pass-debug";
        panel.setAttribute("aria-label", "Polish pass controls");
        panel.innerHTML = ""
            + "<button type=\"button\" class=\"site-pass-debug__toggle\" aria-expanded=\"false\" title=\"Toggle pass controls\">Passes <span class=\"site-pass-debug__badge\" aria-hidden=\"true\"></span></button>"
            + "<div class=\"site-pass-debug__panel\" hidden>"
            + "  <div class=\"site-pass-debug__resize-handle\" title=\"Drag to resize panel width (double-click to reset)\" aria-hidden=\"true\"></div>"
            + "  <div class=\"site-pass-debug__head\" title=\"Drag to move panel (double-click to reset position)\">"
            + "    <span class=\"site-pass-debug__drag-grip\" aria-hidden=\"true\">&#9776;</span>"
            + "    <strong>Visual Polish</strong>"
            + "    <span class=\"site-pass-debug__kind\"></span>"
            + "  </div>"
            + "  <label class=\"site-pass-debug__label\" for=\"site-pass-debug-range\">Pass (1-100)</label>"
            + "  <input id=\"site-pass-debug-range\" class=\"site-pass-debug__range\" type=\"range\" min=\"1\" max=\"100\" step=\"1\">"
            + "  <div class=\"site-pass-debug__row\">"
            + "    <input id=\"site-pass-debug-number\" class=\"site-pass-debug__number\" type=\"number\" min=\"1\" max=\"100\" step=\"1\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-step=\"-10\">-10</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-step=\"10\">+10</button>"
            + "  </div>"
            + "  <div class=\"site-pass-debug__preset-grid\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-preset=\"25\">25</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-preset=\"50\">50</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-preset=\"75\">75</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-preset=\"100\">100</button>"
            + "  </div>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--speed\">"
            + "    <label class=\"site-pass-debug__inline-label\" for=\"site-pass-debug-speed\">Sweep ms</label>"
            + "    <input id=\"site-pass-debug-speed\" class=\"site-pass-debug__speed\" type=\"number\" min=\"25\" max=\"1000\" step=\"5\">"
            + "  </div>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--compact\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"autoplay\">Auto Sweep</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"default\">Use Config</button>"
            + "  </div>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--compact\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"undo\">Undo</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"redo\">Redo</button>"
            + "  </div>"
            + "  <details class=\"site-pass-debug__section\" data-section=\"snapshots\" open>"
            + "  <summary class=\"site-pass-debug__section-head\">Snapshots</summary>"
            + "  <div class=\"site-pass-debug__snapshot-grid\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"save-a\">Save A</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"save-b\">Save B</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"apply-a\">Apply A</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"apply-b\">Apply B</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"toggle-ab\">Flip A/B</button>"
            + "  </div>"
            + "  </details>"
            + "  <details class=\"site-pass-debug__section\" data-section=\"share\">"
            + "  <summary class=\"site-pass-debug__section-head\">Share</summary>"
            + "  <div class=\"site-pass-debug__share-row\">"
            + "    <input id=\"site-pass-debug-share\" class=\"site-pass-debug__share\" type=\"text\" spellcheck=\"false\" aria-label=\"Share pass state URL\">"
            + "  </div>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--compact\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"copy-url\">Copy URL</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"apply-url\">Apply URL</button>"
            + "  </div>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--compact\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"push-url\">Push URL</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"export-json\">Export JSON</button>"
            + "  </div>"
            + "  </details>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--compact\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"reset\">Reset 100</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"close\">Close</button>"
            + "  </div>"
            + "  <details class=\"site-pass-debug__section\" data-section=\"appearance\">"
            + "  <summary class=\"site-pass-debug__section-head\">Appearance</summary>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--speed\">"
            + "    <label class=\"site-pass-debug__inline-label\" for=\"site-pass-debug-opacity\">Opacity %</label>"
            + "    <input id=\"site-pass-debug-opacity\" class=\"site-pass-debug__opacity\" type=\"number\" min=\"20\" max=\"100\" step=\"5\" value=\"100\">"
            + "  </div>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--compact\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn site-pass-debug__btn--toggle\" data-action=\"toggle-blur\">Blur On</button>"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"reset-appearance\">Reset</button>"
            + "  </div>"
            + "  </details>"
            + "  <p class=\"site-pass-debug__meta\">Active: <span class=\"site-pass-debug__value\"></span>/100</p>"
            + "  <p class=\"site-pass-debug__meta\">A/B: <span class=\"site-pass-debug__compare\">A - | B -</span></p>"
            + "  <p class=\"site-pass-debug__meta\">Stack: <span class=\"site-pass-debug__stack\">undo 0 | redo 0</span></p>"
            + "  <p class=\"site-pass-debug__meta\">Sweep: <span class=\"site-pass-debug__sweep\">idle @ 70ms</span></p>"
            + "  <p class=\"site-pass-debug__meta\">Source: <span class=\"site-pass-debug__source\">init</span></p>"
            + "  <details class=\"site-pass-debug__section\" data-section=\"history\">"
            + "  <summary class=\"site-pass-debug__section-head\">History</summary>"
            + "  <div class=\"site-pass-debug__row site-pass-debug__row--compact\">"
            + "    <button type=\"button\" class=\"site-pass-debug__btn\" data-action=\"clear-history\">Clear Log</button>"
            + "  </div>"
            + "  <ol class=\"site-pass-debug__timeline\" aria-live=\"polite\" aria-label=\"Recent pass changes\"></ol>"
            + "  </details>"
            + "  <p class=\"site-pass-debug__hint\">Shortcuts: Alt+Shift+P (panel), Alt+Shift+A (auto), Alt+Shift+1..4 (presets), Alt+Shift+5/6 (A/B), Alt+Shift+7 (flip), Alt+Shift+Z/Y (undo/redo), Alt+Shift+U (apply URL), Alt+Shift+L (push URL), Alt+Shift+I (focus URL), Alt+Shift+H (clear log), Alt+Shift+/ (shortcuts help), arrows (step)</p>"
            + "</div>";

        document.body.appendChild(panel);

        var toggle = panel.querySelector(".site-pass-debug__toggle");
        var bodyPanel = panel.querySelector(".site-pass-debug__panel");
        var kindChip = panel.querySelector(".site-pass-debug__kind");
        var range = panel.querySelector("#site-pass-debug-range");
        var number = panel.querySelector("#site-pass-debug-number");
        var speedInput = panel.querySelector("#site-pass-debug-speed");
        var shareInput = panel.querySelector("#site-pass-debug-share");
        var value = panel.querySelector(".site-pass-debug__value");
        var compareValue = panel.querySelector(".site-pass-debug__compare");
        var stackValue = panel.querySelector(".site-pass-debug__stack");
        var sweepValue = panel.querySelector(".site-pass-debug__sweep");
        var sourceValue = panel.querySelector(".site-pass-debug__source");
        var timeline = panel.querySelector(".site-pass-debug__timeline");
        var stepButtons = panel.querySelectorAll(".site-pass-debug__btn[data-step]");
        var presetButtons = panel.querySelectorAll(".site-pass-debug__btn[data-preset]");
        var resetButton = panel.querySelector('.site-pass-debug__btn[data-action="reset"]');
        var closeButton = panel.querySelector('.site-pass-debug__btn[data-action="close"]');
        var defaultButton = panel.querySelector('.site-pass-debug__btn[data-action="default"]');
        var autoplayButton = panel.querySelector('.site-pass-debug__btn[data-action="autoplay"]');
        var undoButton = panel.querySelector('.site-pass-debug__btn[data-action="undo"]');
        var redoButton = panel.querySelector('.site-pass-debug__btn[data-action="redo"]');
        var saveAButton = panel.querySelector('.site-pass-debug__btn[data-action="save-a"]');
        var saveBButton = panel.querySelector('.site-pass-debug__btn[data-action="save-b"]');
        var applyAButton = panel.querySelector('.site-pass-debug__btn[data-action="apply-a"]');
        var applyBButton = panel.querySelector('.site-pass-debug__btn[data-action="apply-b"]');
        var toggleAbButton = panel.querySelector('.site-pass-debug__btn[data-action="toggle-ab"]');
        var copyUrlButton = panel.querySelector('.site-pass-debug__btn[data-action="copy-url"]');
        var applyUrlButton = panel.querySelector('.site-pass-debug__btn[data-action="apply-url"]');
        var pushUrlButton = panel.querySelector('.site-pass-debug__btn[data-action="push-url"]');
        var clearHistoryButton = panel.querySelector('.site-pass-debug__btn[data-action="clear-history"]');
        var exportJsonButton = panel.querySelector('.site-pass-debug__btn[data-action="export-json"]');
        var toggleBlurButton = panel.querySelector('.site-pass-debug__btn[data-action="toggle-blur"]');
        var resetAppearanceButton = panel.querySelector('.site-pass-debug__btn[data-action="reset-appearance"]');
        var opacityInput = panel.querySelector("#site-pass-debug-opacity");
        var badge = panel.querySelector(".site-pass-debug__badge");
        var dragHead = panel.querySelector(".site-pass-debug__head");
        var resizeHandle = panel.querySelector(".site-pass-debug__resize-handle");

        var queryState = getPassStateFromQuery();
        var queryAuto = shouldAutoplayFromQuery();
        var shouldAutoStart = queryState && queryState.auto !== null ? queryState.auto : queryAuto;
        var configuredPasses = getConfiguredPassCount(kind);
        var currentPasses = initialPassCount;
        var isOpen = false;
        var isAutoplay = false;
        var autoDirection = 1;
        var autoplayTimer = null;
        var autoplayIntervalMs = queryState && Number.isFinite(queryState.sweepMs)
            ? queryState.sweepMs
            : getConfiguredAutoplayInterval(kind);
        var undoStack = (function () {
            var raw = tryLoadValue(getPassUndoStorageKey(kind));
            if (!raw) { return []; }
            try {
                var parsed = JSON.parse(raw);
                return Array.isArray(parsed)
                    ? parsed.filter(function (v) { return Number.isFinite(v); })
                    : [];
            } catch (e) { return []; }
        })();
        var redoStack = [];
        var passHistory = [];
        var snapshots = (function () {
            var raw = tryLoadValue(getPassSnapshotStorageKey(kind));
            if (!raw) {
                return { a: null, b: null };
            }

            try {
                var parsed = JSON.parse(raw);
                return {
                    a: toValidPass(parsed && parsed.a),
                    b: toValidPass(parsed && parsed.b)
                };
            } catch (error) {
                return { a: null, b: null };
            }
        })();

        if (queryState && Number.isFinite(queryState.passCount)) {
            currentPasses = queryState.passCount;
        }

        if (queryState && queryState.snapshotA !== null) {
            snapshots.a = queryState.snapshotA;
        }

        if (queryState && queryState.snapshotB !== null) {
            snapshots.b = queryState.snapshotB;
        }

        var savedOpen = tryLoadValue(DEBUG_OPEN_STORAGE_KEY);
        var queryOpen = shouldOpenDebugFromQuery();
        if (queryState && queryState.open !== null) {
            isOpen = queryState.open;
        } else if (queryOpen !== null) {
            isOpen = queryOpen;
        } else if (savedOpen === "1") {
            isOpen = true;
        }

        kindChip.textContent = kind.toUpperCase();

        function persistPass(passCount) {
            trySaveValue(getPassStorageKey(kind), String(passCount));
            trySaveValue(PASS_STORAGE_KEY, String(passCount));
        }

        function persistSnapshots() {
            trySaveValue(getPassSnapshotStorageKey(kind), JSON.stringify({
                a: snapshots.a,
                b: snapshots.b
            }));
        }

        function persistUndoStacks() {
            trySaveValue(getPassUndoStorageKey(kind), JSON.stringify(undoStack));
        }

        function serializePassState() {
            return {
                pass: currentPasses,
                speed: autoplayIntervalMs,
                a: snapshots.a,
                b: snapshots.b,
                open: isOpen,
                auto: isAutoplay
            };
        }

        function buildShareUrl() {
            var url = new URL(window.location.href);
            var params = url.searchParams;
            var cleanupKeys = [
                "pass",
                "passes",
                "passpanel",
                "debugpasses",
                "passdebug",
                "passsweepms",
                "passautoplayms",
                "passspeed",
                "passauto",
                "passautoplay",
                "autosweep",
                "passstate"
            ];

            cleanupKeys.forEach(function (key) {
                params.delete(key);
            });

            params.set("passstate", JSON.stringify(serializePassState()));
            return url.toString();
        }

        function syncShareUrlField() {
            if (!shareInput) {
                return;
            }

            shareInput.value = buildShareUrl();
        }

        function syncSourceLabel(source) {
            sourceValue.textContent = normalizePassSource(source);
        }

        function syncSweepLabel() {
            if (!sweepValue) {
                return;
            }

            sweepValue.textContent = (isAutoplay ? "running" : "idle") + " @ " + autoplayIntervalMs + "ms";
        }

        function syncUndoState() {
            if (!stackValue) {
                return;
            }

            stackValue.textContent = "undo " + undoStack.length + " | redo " + redoStack.length;
            undoButton.disabled = undoStack.length === 0;
            redoButton.disabled = redoStack.length === 0;
        }

        function shouldTrackUndo(source, nextPass) {
            if (!Number.isFinite(nextPass) || nextPass === currentPasses) {
                return false;
            }

            var normalized = String(source || "panel");
            if (normalized === "autoplay" || normalized.indexOf("undo") !== -1 || normalized.indexOf("redo") !== -1 || normalized === "state-init" || normalized === "event") {
                return false;
            }

            return true;
        }

        function pushUndo(previousPass) {
            undoStack.push(previousPass);
            if (undoStack.length > PASS_MAX) {
                undoStack.shift();
            }
            redoStack = [];
            persistUndoStacks();
            syncUndoState();
        }

        function runUndo(source) {
            if (!undoStack.length) {
                return;
            }

            var targetPass = undoStack.pop();
            if (targetPass === currentPasses) {
                persistUndoStacks();
                syncUndoState();
                return;
            }

            redoStack.push(currentPasses);
            if (redoStack.length > PASS_MAX) {
                redoStack.shift();
            }

            persistUndoStacks();
            applyPassCount(targetPass, true, source || "undo");
            syncUndoState();
        }

        function runRedo(source) {
            if (!redoStack.length) {
                return;
            }

            var targetPass = redoStack.pop();
            if (targetPass === currentPasses) {
                persistUndoStacks();
                syncUndoState();
                return;
            }

            undoStack.push(currentPasses);
            if (undoStack.length > PASS_MAX) {
                undoStack.shift();
            }

            persistUndoStacks();
            applyPassCount(targetPass, true, source || "redo");
            syncUndoState();
        }

        function renderHistory() {
            if (!timeline) {
                return;
            }

            timeline.innerHTML = "";

            if (!passHistory.length) {
                var empty = document.createElement("li");
                empty.className = "site-pass-debug__timeline-item is-empty";
                empty.textContent = "No pass changes yet";
                timeline.appendChild(empty);
                return;
            }

            passHistory.forEach(function (entry) {
                var item = document.createElement("li");
                item.className = "site-pass-debug__timeline-item site-pass-debug__timeline-item--restore";
                item.tabIndex = 0;
                item.setAttribute("role", "button");
                item.title = "Restore pass " + entry.pass;
                item.setAttribute("aria-label", "Restore " + entry.pass + " passes (" + entry.source + ")");

                var stamp = document.createElement("span");
                stamp.className = "site-pass-debug__timeline-time";
                stamp.textContent = entry.stamp;

                var detail = document.createElement("span");
                detail.className = "site-pass-debug__timeline-detail";
                var deltaText = entry.delta === null ? "" : " (" + (entry.delta >= 0 ? "+" : "") + entry.delta + ")";
                detail.textContent = entry.source + " -> " + entry.pass + deltaText;

                item.appendChild(stamp);
                item.appendChild(detail);

                (function (passValue) {
                    function handleRestore(evt) {
                        if (evt.type === "keydown" && evt.key !== "Enter" && evt.key !== " ") {
                            return;
                        }
                        if (evt.key === " ") {
                            evt.preventDefault();
                        }
                        applyPassCount(passValue, true, "timeline-restore");
                    }
                    item.addEventListener("click", handleRestore);
                    item.addEventListener("keydown", handleRestore);
                })(entry.pass);

                timeline.appendChild(item);
            });
        }

        function pushHistory(passCount, source) {
            var normalizedSource = normalizePassSource(source || "event");
            var now = new Date();
            var stamp = now.toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            });

            var top = passHistory[0];
            if (top && normalizedSource === "autoplay" && top.source === "autoplay") {
                var autoplayPrev = top.pass;
                top.pass = passCount;
                top.stamp = stamp;
                top.delta = passCount - autoplayPrev;
                renderHistory();
                return;
            }

            if (top && top.pass === passCount && top.source === normalizedSource) {
                return;
            }

            var previousPass = top ? top.pass : null;
            passHistory.unshift({
                pass: passCount,
                source: normalizedSource,
                stamp: stamp,
                delta: previousPass === null ? null : passCount - previousPass
            });

            if (passHistory.length > PASS_HISTORY_MAX) {
                passHistory.length = PASS_HISTORY_MAX;
            }

            renderHistory();
        }

        function clearHistory(sourceLabel) {
            passHistory = [];
            renderHistory();
            syncSourceLabel(sourceLabel || "history-clear");
        }

        function syncSnapshotUI(passCount) {
            var hasA = Number.isFinite(snapshots.a);
            var hasB = Number.isFinite(snapshots.b);

            applyAButton.disabled = !hasA;
            applyBButton.disabled = !hasB;
            toggleAbButton.disabled = !hasA && !hasB;

            saveAButton.classList.toggle("is-active", hasA && snapshots.a === passCount);
            saveBButton.classList.toggle("is-active", hasB && snapshots.b === passCount);

            if (hasA || hasB) {
                var nextLabel = "A";
                if (hasA && hasB) {
                    nextLabel = passCount === snapshots.a ? "B" : "A";
                } else if (hasB && !hasA) {
                    nextLabel = "B";
                }
                toggleAbButton.textContent = "Flip " + nextLabel;
            } else {
                toggleAbButton.textContent = "Flip A/B";
            }

            if (hasA && hasB) {
                var delta = snapshots.b - snapshots.a;
                compareValue.textContent = "A " + snapshots.a + " | B " + snapshots.b + " | Δ " + (delta >= 0 ? "+" : "") + delta;
            } else {
                compareValue.textContent = "A " + (hasA ? snapshots.a : "-") + " | B " + (hasB ? snapshots.b : "-");
            }

            syncShareUrlField();
        }

        function applySnapshotToggle(source) {
            var hasA = Number.isFinite(snapshots.a);
            var hasB = Number.isFinite(snapshots.b);

            if (!hasA && !hasB) {
                return;
            }

            if (hasA && hasB) {
                var target = currentPasses === snapshots.a ? snapshots.b : snapshots.a;
                applyPassCount(target, true, source || "snapshot-toggle");
                return;
            }

            applyPassCount(hasA ? snapshots.a : snapshots.b, true, source || "snapshot-toggle");
        }

        function applyStatePayload(rawState, sourceLabel) {
            var state = normalizePassState(rawState);
            if (!state) {
                return false;
            }

            if (state.sweepMs !== null) {
                setAutoplayInterval(state.sweepMs, true);
            }

            if (state.snapshotA !== null) {
                snapshots.a = state.snapshotA;
            }

            if (state.snapshotB !== null) {
                snapshots.b = state.snapshotB;
            }

            persistSnapshots();

            if (state.passCount !== null) {
                applyPassCount(state.passCount, true, sourceLabel || "state");
            } else {
                syncInputs(currentPasses);
                syncSourceLabel(sourceLabel || "state");
            }

            if (state.open !== null) {
                setPanelOpen(state.open);
            }

            if (state.auto !== null) {
                if (state.auto) {
                    startAutoplay();
                } else {
                    stopAutoplay();
                }
            }

            syncShareUrlField();
            return true;
        }

        function setAutoplayInterval(rawInterval, persistSelection) {
            var normalized = toValidSpeed(rawInterval);
            if (!Number.isFinite(normalized)) {
                normalized = PASS_AUTOPLAY_INTERVAL_MS;
            }

            autoplayIntervalMs = normalized;
            speedInput.value = String(autoplayIntervalMs);

            if (persistSelection) {
                trySaveValue(getPassSpeedStorageKey(kind), String(autoplayIntervalMs));
                trySaveValue(PASS_AUTOPLAY_STORAGE_KEY, String(autoplayIntervalMs));
            }

            if (isAutoplay) {
                startAutoplay();
            }

            syncSweepLabel();
            syncShareUrlField();
        }

        function syncInputs(passCount) {
            range.value = String(passCount);
            number.value = String(passCount);
            value.textContent = String(passCount);
            if (badge) { badge.textContent = String(passCount); }

            presetButtons.forEach(function (button) {
                var preset = Number(button.getAttribute("data-preset"));
                button.classList.toggle("is-active", preset === passCount);
            });

            syncSnapshotUI(passCount);
        }

        function stopAutoplay() {
            if (autoplayTimer) {
                clearInterval(autoplayTimer);
                autoplayTimer = null;
            }
            isAutoplay = false;
            autoplayButton.textContent = "Auto Sweep";
            autoplayButton.classList.remove("is-active");
            syncSweepLabel();
            syncShareUrlField();
        }

        function startAutoplay() {
            if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
                return;
            }

            stopAutoplay();
            isAutoplay = true;
            autoplayButton.textContent = "Stop Sweep";
            autoplayButton.classList.add("is-active");
            syncSweepLabel();
            syncShareUrlField();

            autoplayTimer = setInterval(function () {
                if (currentPasses >= PASS_MAX) {
                    autoDirection = -1;
                } else if (currentPasses <= PASS_MIN) {
                    autoDirection = 1;
                }

                applyPassCount(currentPasses + autoDirection, true, "autoplay");
            }, autoplayIntervalMs);
        }

        function toggleAutoplay() {
            if (isAutoplay) {
                stopAutoplay();
                return;
            }

            startAutoplay();
        }

        function isEditableTarget(target) {
            if (!target) {
                return false;
            }

            if (target.isContentEditable) {
                return true;
            }

            var tag = (target.tagName || "").toLowerCase();
            return tag === "input" || tag === "textarea" || tag === "select";
        }

        function syncFromPassEvent(event) {
            if (!event || !event.detail || event.detail.kind !== kind) {
                return;
            }

            var detailPassCount = Number(event.detail.passCount);
            if (!Number.isFinite(detailPassCount)) {
                return;
            }

            currentPasses = Math.round(clamp(detailPassCount, PASS_MIN, PASS_MAX));
            syncInputs(currentPasses);
            syncSourceLabel(event.detail.source || "event");
            pushHistory(currentPasses, event.detail.source || "event");
        }

        function setPanelOpen(nextOpen) {
            isOpen = !!nextOpen;
            panel.classList.toggle("is-open", isOpen);
            bodyPanel.hidden = !isOpen;
            toggle.setAttribute("aria-expanded", String(isOpen));
            trySaveValue(DEBUG_OPEN_STORAGE_KEY, isOpen ? "1" : "0");

            if (!isOpen) {
                stopAutoplay();
            }

            syncShareUrlField();
        }

        function applyPassCount(rawPassCount, persistSelection, source) {
            var normalized = Math.round(clamp(Number(rawPassCount), PASS_MIN, PASS_MAX));
            var effectiveSource = source || "panel";

            if (shouldTrackUndo(effectiveSource, normalized)) {
                pushUndo(currentPasses);
            }

            currentPasses = runPolishPasses(kind, normalized, effectiveSource);
            syncInputs(currentPasses);
            syncSourceLabel(effectiveSource);

            if (persistSelection) {
                persistPass(currentPasses);
            }

            syncUndoState();
            syncShareUrlField();
        }

        toggle.addEventListener("click", function () {
            setPanelOpen(!isOpen);
        });

        range.addEventListener("input", function () {
            applyPassCount(range.value, true, "slider");
        });

        number.addEventListener("change", function () {
            applyPassCount(number.value, true, "number");
        });

        speedInput.addEventListener("change", function () {
            setAutoplayInterval(speedInput.value, true);
            syncSourceLabel("speed");
        });

        stepButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                var delta = Number(button.getAttribute("data-step"));
                applyPassCount(currentPasses + delta, true, "step");
            });
        });

        presetButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                var preset = Number(button.getAttribute("data-preset"));
                applyPassCount(preset, true, "preset");
            });
        });

        resetButton.addEventListener("click", function () {
            applyPassCount(PASS_MAX, true, "reset");
        });

        defaultButton.addEventListener("click", function () {
            configuredPasses = getConfiguredPassCount(kind);
            applyPassCount(configuredPasses, true, "default");
        });

        autoplayButton.addEventListener("click", function () {
            toggleAutoplay();
        });

        undoButton.addEventListener("click", function () {
            runUndo("undo");
        });

        redoButton.addEventListener("click", function () {
            runRedo("redo");
        });

        saveAButton.addEventListener("click", function () {
            snapshots.a = currentPasses;
            persistSnapshots();
            syncSnapshotUI(currentPasses);
            syncSourceLabel("save-a");
        });

        saveBButton.addEventListener("click", function () {
            snapshots.b = currentPasses;
            persistSnapshots();
            syncSnapshotUI(currentPasses);
            syncSourceLabel("save-b");
        });

        applyAButton.addEventListener("click", function () {
            if (Number.isFinite(snapshots.a)) {
                applyPassCount(snapshots.a, true, "snapshot-a");
            }
        });

        applyBButton.addEventListener("click", function () {
            if (Number.isFinite(snapshots.b)) {
                applyPassCount(snapshots.b, true, "snapshot-b");
            }
        });

        toggleAbButton.addEventListener("click", function () {
            applySnapshotToggle("snapshot-toggle");
        });

        copyUrlButton.addEventListener("click", function () {
            var shareUrl = buildShareUrl();
            shareInput.value = shareUrl;

            if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
                navigator.clipboard.writeText(shareUrl)
                    .then(function () {
                        syncSourceLabel("share-copied");
                    })
                    .catch(function () {
                        syncSourceLabel("share-copy-failed");
                    });
                return;
            }

            shareInput.focus();
            shareInput.select();
            syncSourceLabel("share-ready");
        });

        applyUrlButton.addEventListener("click", function () {
            var parsed = parsePassStateFromInput(shareInput.value);
            var applied = applyStatePayload(parsed, "share-import");
            if (!applied) {
                syncSourceLabel("share-invalid");
            }
        });

        pushUrlButton.addEventListener("click", function () {
            var shareUrl = buildShareUrl();
            if (window.history && typeof window.history.replaceState === "function") {
                window.history.replaceState({}, "", shareUrl);
                syncShareUrlField();
                syncSourceLabel("url-pushed");
                return;
            }

            shareInput.value = shareUrl;
            syncSourceLabel("url-ready");
        });

        clearHistoryButton.addEventListener("click", function () {
            clearHistory("history-clear");
        });

        shareInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter") {
                event.preventDefault();
                applyUrlButton.click();
            }
        });

        closeButton.addEventListener("click", function () {
            setPanelOpen(false);
        });

        document.addEventListener("site-upgrade:pass-change", syncFromPassEvent);

        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                stopAutoplay();
            }
        });

        window.addEventListener("beforeunload", stopAutoplay);

        document.addEventListener("keydown", function (event) {
            if (shortcutOverlay && event.key === "Escape") {
                event.preventDefault();
                hideShortcutOverlay();
                return;
            }

            if (isEditableTarget(event.target)) {
                return;
            }

            if (!(event.altKey && event.shiftKey)) {
                return;
            }

            if (event.key.toLowerCase() === "p") {
                event.preventDefault();
                setPanelOpen(!isOpen);
                return;
            }

            if (event.key.toLowerCase() === "a") {
                event.preventDefault();
                toggleAutoplay();
                return;
            }

            if (event.key.toLowerCase() === "c") {
                event.preventDefault();
                setPanelOpen(false);
                return;
            }

            if (event.code === "Digit0") {
                event.preventDefault();
                applyPassCount(PASS_MAX, true, "shortcut-reset");
                return;
            }

            if (event.code === "Digit1" || event.code === "Digit2" || event.code === "Digit3" || event.code === "Digit4") {
                event.preventDefault();
                var presetMap = {
                    Digit1: 25,
                    Digit2: 50,
                    Digit3: 75,
                    Digit4: 100
                };
                applyPassCount(presetMap[event.code], true, "shortcut-preset");
                return;
            }

            if (event.code === "Digit5") {
                event.preventDefault();
                if (Number.isFinite(snapshots.a)) {
                    applyPassCount(snapshots.a, true, "shortcut-a");
                }
                return;
            }

            if (event.code === "Digit6") {
                event.preventDefault();
                if (Number.isFinite(snapshots.b)) {
                    applyPassCount(snapshots.b, true, "shortcut-b");
                }
                return;
            }

            if (event.code === "Digit7") {
                event.preventDefault();
                applySnapshotToggle("shortcut-toggle");
                return;
            }

            if (event.key.toLowerCase() === "u") {
                event.preventDefault();
                applyUrlButton.click();
                return;
            }

            if (event.key.toLowerCase() === "i") {
                event.preventDefault();
                shareInput.focus();
                shareInput.select();
                syncSourceLabel("url-focus");
                return;
            }

            if (event.key.toLowerCase() === "h") {
                event.preventDefault();
                clearHistory("history-clear");
                return;
            }

            if (event.key === "/") {
                event.preventDefault();
                if (shortcutOverlay) {
                    hideShortcutOverlay();
                } else {
                    showShortcutOverlay();
                }
                return;
            }

            if (event.key.toLowerCase() === "l") {
                event.preventDefault();
                pushUrlButton.click();
                return;
            }

            if (event.key.toLowerCase() === "z") {
                event.preventDefault();
                runUndo("shortcut-undo");
                return;
            }

            if (event.key.toLowerCase() === "y") {
                event.preventDefault();
                runRedo("shortcut-redo");
                return;
            }

            if (event.key === "ArrowUp") {
                event.preventDefault();
                applyPassCount(currentPasses + 1, true, "shortcut-up");
                return;
            }

            if (event.key === "ArrowDown") {
                event.preventDefault();
                applyPassCount(currentPasses - 1, true, "shortcut-down");
                return;
            }

            if (event.key === "ArrowRight") {
                event.preventDefault();
                applyPassCount(currentPasses + 10, true, "shortcut-right");
                return;
            }

            if (event.key === "ArrowLeft") {
                event.preventDefault();
                applyPassCount(currentPasses - 10, true, "shortcut-left");
            }
        });

        setAutoplayInterval(autoplayIntervalMs, false);
        syncSweepLabel();
        syncInputs(currentPasses);
        syncUndoState();
        syncShareUrlField();
        renderHistory();

        if (queryState && (queryState.snapshotA !== null || queryState.snapshotB !== null)) {
            persistSnapshots();
        }

        if (currentPasses !== initialPassCount) {
            applyPassCount(currentPasses, true, "state-init");
        } else {
            syncSourceLabel("init");
            pushHistory(currentPasses, "init");
        }

        setPanelOpen(isOpen);

        if (shouldAutoStart === true) {
            startAutoplay();
        } else if (shouldAutoStart === false) {
            stopAutoplay();
        }

        // --- Drag to reposition ---
        (function () {
            var savedPos = (function () {
                var raw = tryLoadValue(getPassPositionStorageKey(kind));
                if (!raw) { return null; }
                try {
                    var p = JSON.parse(raw);
                    return p && Number.isFinite(p.right) && Number.isFinite(p.bottom) ? p : null;
                } catch (e) { return null; }
            })();

            function applyPosition(right, bottom) {
                var maxRight = window.innerWidth - 40;
                var maxBottom = window.innerHeight - 40;
                var r = Math.min(Math.max(right, 0), maxRight);
                var b = Math.min(Math.max(bottom, 0), maxBottom);
                panel.style.right = r + "px";
                panel.style.bottom = b + "px";
            }

            function resetPosition() {
                panel.style.right = "";
                panel.style.bottom = "";
                try { localStorage.removeItem(getPassPositionStorageKey(kind)); } catch (e) { /* */ }
            }

            if (savedPos) {
                applyPosition(savedPos.right, savedPos.bottom);
            }

            var dragState = null;

            dragHead.addEventListener("mousedown", function (evt) {
                if (evt.target && (evt.target.tagName === "BUTTON" || evt.target.tagName === "INPUT" || evt.target.tagName === "SUMMARY")) {
                    return;
                }
                evt.preventDefault();
                var rect = panel.getBoundingClientRect();
                dragState = {
                    startX: evt.clientX,
                    startY: evt.clientY,
                    startRight: window.innerWidth - rect.right,
                    startBottom: window.innerHeight - rect.bottom
                };
                panel.classList.add("is-dragging");
            });

            document.addEventListener("mousemove", function (evt) {
                if (!dragState) { return; }
                var dx = evt.clientX - dragState.startX;
                var dy = evt.clientY - dragState.startY;
                applyPosition(dragState.startRight - dx, dragState.startBottom - dy);
            });

            document.addEventListener("mouseup", function (evt) {
                if (!dragState) { return; }
                panel.classList.remove("is-dragging");
                var rect = panel.getBoundingClientRect();
                var finalRight = window.innerWidth - rect.right;
                var finalBottom = window.innerHeight - rect.bottom;
                trySaveValue(getPassPositionStorageKey(kind), JSON.stringify({ right: finalRight, bottom: finalBottom }));
                dragState = null;
            });

            dragHead.addEventListener("touchstart", function (evt) {
                if (evt.touches.length !== 1) { return; }
                if (evt.target && (evt.target.tagName === "BUTTON" || evt.target.tagName === "INPUT" || evt.target.tagName === "SUMMARY")) {
                    return;
                }
                var touch = evt.touches[0];
                var rect = panel.getBoundingClientRect();
                dragState = {
                    startX: touch.clientX,
                    startY: touch.clientY,
                    startRight: window.innerWidth - rect.right,
                    startBottom: window.innerHeight - rect.bottom
                };
                panel.classList.add("is-dragging");
            }, { passive: true });

            document.addEventListener("touchmove", function (evt) {
                if (!dragState) { return; }
                if (evt.cancelable) { evt.preventDefault(); }
                var touch = evt.touches[0];
                var dx = touch.clientX - dragState.startX;
                var dy = touch.clientY - dragState.startY;
                applyPosition(dragState.startRight - dx, dragState.startBottom - dy);
            }, { passive: false });

            document.addEventListener("touchend", function () {
                if (!dragState) { return; }
                panel.classList.remove("is-dragging");
                var rect = panel.getBoundingClientRect();
                var finalRight = window.innerWidth - rect.right;
                var finalBottom = window.innerHeight - rect.bottom;
                trySaveValue(getPassPositionStorageKey(kind), JSON.stringify({ right: finalRight, bottom: finalBottom }));
                dragState = null;
            });

            dragHead.addEventListener("dblclick", function (evt) {
                if (evt.target && (evt.target.tagName === "BUTTON" || evt.target.tagName === "INPUT")) {
                    return;
                }
                resetPosition();
            });
        })();

        // --- Shortcut cheat-sheet overlay ---
        var shortcutOverlay = null;

        function showShortcutOverlay() {
            if (shortcutOverlay) { return; }
            shortcutOverlay = document.createElement("div");
            shortcutOverlay.className = "site-pass-shortcut-overlay";
            shortcutOverlay.setAttribute("role", "dialog");
            shortcutOverlay.setAttribute("aria-modal", "true");
            shortcutOverlay.setAttribute("aria-label", "Keyboard shortcuts");
            shortcutOverlay.innerHTML = ""
                + "<div class=\"site-pass-shortcut-overlay__box\">"
                + "<div class=\"site-pass-shortcut-overlay__head\">"
                + "<strong>Keyboard Shortcuts</strong>"
                + "<button type=\"button\" class=\"site-pass-shortcut-overlay__close\" aria-label=\"Close shortcuts\">&#10005;</button>"
                + "</div>"
                + "<dl class=\"site-pass-shortcut-overlay__list\">"
                + "<dt>Alt+Shift+P</dt><dd>Toggle panel</dd>"
                + "<dt>Alt+Shift+A</dt><dd>Toggle auto sweep</dd>"
                + "<dt>Alt+Shift+C</dt><dd>Close panel</dd>"
                + "<dt>Alt+Shift+1&ndash;4</dt><dd>Presets 25 / 50 / 75 / 100</dd>"
                + "<dt>Alt+Shift+0</dt><dd>Reset to 100</dd>"
                + "<dt>Alt+Shift+5</dt><dd>Apply snapshot A</dd>"
                + "<dt>Alt+Shift+6</dt><dd>Apply snapshot B</dd>"
                + "<dt>Alt+Shift+7</dt><dd>Flip A/B</dd>"
                + "<dt>Alt+Shift+Z</dt><dd>Undo</dd>"
                + "<dt>Alt+Shift+Y</dt><dd>Redo</dd>"
                + "<dt>Alt+Shift+U</dt><dd>Apply URL state</dd>"
                + "<dt>Alt+Shift+L</dt><dd>Push URL state</dd>"
                + "<dt>Alt+Shift+I</dt><dd>Focus URL input</dd>"
                + "<dt>Alt+Shift+H</dt><dd>Clear history log</dd>"
                + "<dt>Alt+Shift+/</dt><dd>Show this overlay</dd>"
                + "<dt>Arrow Up / Right</dt><dd>+1 / +10 passes</dd>"
                + "<dt>Arrow Down / Left</dt><dd>&minus;1 / &minus;10 passes</dd>"
                + "</dl>"
                + "<p class=\"site-pass-shortcut-overlay__tip\">Double-click panel header to reset position</p>"
                + "</div>";
            document.body.appendChild(shortcutOverlay);
            var closeBtn = shortcutOverlay.querySelector(".site-pass-shortcut-overlay__close");
            if (closeBtn) { closeBtn.focus(); }

            function dismissOverlay(evt) {
                if (!shortcutOverlay) { return; }
                var box = shortcutOverlay.querySelector(".site-pass-shortcut-overlay__box");
                if (!box || !box.contains(evt.target)) {
                    hideShortcutOverlay();
                }
            }
            shortcutOverlay._dismiss = dismissOverlay;
            shortcutOverlay.addEventListener("click", dismissOverlay);
            if (closeBtn) {
                closeBtn.addEventListener("click", function () { hideShortcutOverlay(); });
            }
        }

        function hideShortcutOverlay() {
            if (!shortcutOverlay) { return; }
            shortcutOverlay.remove();
            shortcutOverlay = null;
        }

        var sectionEls = panel.querySelectorAll(".site-pass-debug__section");
        var savedSections = (function () {
            var raw = tryLoadValue(getPassSectionsStorageKey(kind));
            if (!raw) { return null; }
            try { return JSON.parse(raw); } catch (e) { return null; }
        })();

        if (savedSections) {
            sectionEls.forEach(function (el) {
                var name = el.getAttribute("data-section");
                if (name && Object.prototype.hasOwnProperty.call(savedSections, name)) {
                    if (savedSections[name]) {
                        el.setAttribute("open", "");
                    } else {
                        el.removeAttribute("open");
                    }
                }
            });
        }

        // Animated details open/close
        function animateDetails(el, opening) {
            var inner = el.querySelector("summary + *") || el.querySelector("summary");
            if (!inner) {
                return;
            }

            // Respect reduced-motion preference — skip animation
            var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

            if (el._animating) {
                clearTimeout(el._animating);
                el._animating = null;
                if (el._innerEl) { el._innerEl.style.height = ""; el._innerEl.style.overflow = ""; }
            }

            var wrapper = el._innerEl;
            if (!wrapper) {
                // Wrap all non-summary children in an animate wrapper once
                wrapper = document.createElement("div");
                wrapper.className = "site-pass-debug__section-body";
                var children = Array.prototype.slice.call(el.childNodes);
                children.forEach(function (node) {
                    if (node.nodeType === 1 && node.tagName === "SUMMARY") { return; }
                    wrapper.appendChild(node);
                });
                el.appendChild(wrapper);
                el._innerEl = wrapper;
            }

            if (prefersReduced) {
                wrapper.style.height = "";
                wrapper.style.overflow = "";
                return;
            }

            var targetHeight = opening ? wrapper.scrollHeight + "px" : "0px";
            wrapper.style.overflow = "hidden";
            wrapper.style.height = opening ? "0px" : wrapper.scrollHeight + "px";

            // Force reflow
            void wrapper.offsetHeight;
            wrapper.style.transition = "height 0.2s ease";
            wrapper.style.height = targetHeight;

            var DURATION = 210;
            el._animating = setTimeout(function () {
                wrapper.style.transition = "";
                wrapper.style.overflow = "";
                if (opening) { wrapper.style.height = ""; }
                el._animating = null;
            }, DURATION);
        }

        sectionEls.forEach(function (el) {
            // Intercept toggle: cancel default, run animation, then commit open state
            el.addEventListener("click", function (evt) {
                if (evt.target && evt.target.tagName === "SUMMARY") {
                    evt.preventDefault();
                    var willOpen = !el.open;
                    if (willOpen) { el.setAttribute("open", ""); }
                    animateDetails(el, willOpen);
                    if (!willOpen) {
                        setTimeout(function () { el.removeAttribute("open"); }, 200);
                    }
                    var state = {};
                    sectionEls.forEach(function (s) {
                        var sName = s.getAttribute("data-section");
                        if (sName) { state[sName] = willOpen ? true : false; }
                    });
                    // Only update the toggled section
                    var secName = el.getAttribute("data-section");
                    var fullState = {};
                    sectionEls.forEach(function (s) {
                        var n = s.getAttribute("data-section");
                        if (n) { fullState[n] = n === secName ? willOpen : s.open; }
                    });
                    trySaveValue(getPassSectionsStorageKey(kind), JSON.stringify(fullState));
                }
            });
        });

        // --- Panel width resize handle ---
        (function () {
            var PANEL_MIN_W = 220;
            var PANEL_MAX_W = Math.min(560, window.innerWidth - 28);
            var savedWidth = (function () {
                var raw = tryLoadValue(getPassWidthStorageKey(kind));
                var v = raw ? parseFloat(raw) : NaN;
                return Number.isFinite(v) ? v : null;
            })();

            var innerPanel = panel.querySelector(".site-pass-debug__panel");

            function applyWidth(w) {
                var clamped = Math.min(Math.max(w, PANEL_MIN_W), Math.min(560, window.innerWidth - 28));
                innerPanel.style.width = clamped + "px";
                return clamped;
            }

            function resetWidth() {
                innerPanel.style.width = "";
                try { localStorage.removeItem(getPassWidthStorageKey(kind)); } catch (e) { /* */ }
            }

            if (savedWidth) {
                applyWidth(savedWidth);
            }

            var resizeDrag = null;

            resizeHandle.addEventListener("mousedown", function (evt) {
                evt.preventDefault();
                var rect = innerPanel.getBoundingClientRect();
                resizeDrag = { startX: evt.clientX, startWidth: rect.width };
                panel.classList.add("is-resizing");
            });

            document.addEventListener("mousemove", function (evt) {
                if (!resizeDrag) { return; }
                // Handle is on the left edge — drag left = wider, drag right = narrower
                var dx = resizeDrag.startX - evt.clientX;
                applyWidth(resizeDrag.startWidth + dx);
            });

            document.addEventListener("mouseup", function () {
                if (!resizeDrag) { return; }
                panel.classList.remove("is-resizing");
                var finalWidth = parseFloat(innerPanel.style.width) || null;
                if (finalWidth) {
                    trySaveValue(getPassWidthStorageKey(kind), String(finalWidth));
                }
                resizeDrag = null;
            });

            resizeHandle.addEventListener("dblclick", function () {
                resetWidth();
            });
        })();

        if (exportJsonButton) {
            exportJsonButton.addEventListener("click", function () {
                var json = JSON.stringify(serializePassState(), null, 2);
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(json).then(function () {
                        var orig = exportJsonButton.textContent;
                        exportJsonButton.textContent = "Copied!";
                        setTimeout(function () { exportJsonButton.textContent = orig; }, 1200);
                    }).catch(function () {
                        shareInput.value = json;
                        shareInput.select();
                    });
                } else {
                    shareInput.value = json;
                    shareInput.select();
                }
            });
        }

        // --- Appearance controls (opacity / blur) ---
        (function () {
            var innerPanel = panel.querySelector(".site-pass-debug__panel");
            var blurEnabled = true;

            var saved = (function () {
                var raw = tryLoadValue(getPassPanelStyleStorageKey(kind));
                if (!raw) { return null; }
                try { return JSON.parse(raw); } catch (e) { return null; }
            })();

            var currentOpacity = (saved && Number.isFinite(saved.opacity)) ? saved.opacity : 100;
            var currentBlur = (saved && typeof saved.blur === "boolean") ? saved.blur : true;
            blurEnabled = currentBlur;

            function applyAppearance(opacity, blur) {
                innerPanel.style.opacity = (opacity / 100).toFixed(2);
                innerPanel.style.backdropFilter = blur ? "blur(10px)" : "none";
                innerPanel.style.webkitBackdropFilter = blur ? "blur(10px)" : "none";
            }

            function syncAppearanceUI() {
                if (opacityInput) { opacityInput.value = String(currentOpacity); }
                if (toggleBlurButton) {
                    toggleBlurButton.textContent = blurEnabled ? "Blur On" : "Blur Off";
                    toggleBlurButton.classList.toggle("is-active", blurEnabled);
                }
            }

            function persistAppearance() {
                trySaveValue(getPassPanelStyleStorageKey(kind), JSON.stringify({ opacity: currentOpacity, blur: blurEnabled }));
            }

            applyAppearance(currentOpacity, blurEnabled);
            syncAppearanceUI();

            if (opacityInput) {
                opacityInput.addEventListener("change", function () {
                    var v = Math.min(100, Math.max(20, Number(opacityInput.value) || 100));
                    currentOpacity = v;
                    opacityInput.value = String(v);
                    applyAppearance(currentOpacity, blurEnabled);
                    persistAppearance();
                });
                opacityInput.addEventListener("input", function () {
                    var v = Math.min(100, Math.max(20, Number(opacityInput.value) || 100));
                    applyAppearance(v, blurEnabled);
                });
            }

            if (toggleBlurButton) {
                toggleBlurButton.addEventListener("click", function () {
                    blurEnabled = !blurEnabled;
                    applyAppearance(currentOpacity, blurEnabled);
                    syncAppearanceUI();
                    persistAppearance();
                });
            }

            if (resetAppearanceButton) {
                resetAppearanceButton.addEventListener("click", function () {
                    currentOpacity = 100;
                    blurEnabled = true;
                    applyAppearance(currentOpacity, blurEnabled);
                    syncAppearanceUI();
                    try { localStorage.removeItem(getPassPanelStyleStorageKey(kind)); } catch (e) { /* */ }
                });
            }
        })();
    }

    function ensureSkipLink() {
        if (document.querySelector(".site-upgrade-skip")) {
            return;
        }

        var candidates = ["main", "#mainContent", ".main", ".page", ".container", ".content"];
        var target = null;

        for (var i = 0; i < candidates.length; i += 1) {
            var element = document.querySelector(candidates[i]);
            if (element) {
                target = element;
                break;
            }
        }

        if (!target) {
            return;
        }

        if (!target.id) {
            target.id = "site-upgrade-main";
        }

        var skip = document.createElement("a");
        skip.className = "site-upgrade-skip";
        skip.href = "#" + target.id;
        skip.textContent = "Skip to main content";
        document.body.prepend(skip);
    }

    function upgradeExternalLinks() {
        var links = document.querySelectorAll('a[target="_blank"]');
        links.forEach(function (link) {
            var rel = (link.getAttribute("rel") || "").toLowerCase();
            if (!rel.includes("noopener")) {
                link.setAttribute("rel", (rel ? rel + " " : "") + "noopener noreferrer");
            }
        });
    }

    function applyRevealAnimations() {
        if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            return;
        }

        var selectors = [
            "section",
            ".card",
            ".hero-card",
            ".feature-card",
            ".system-card",
            ".welcome-card",
            ".route-card",
            ".signal-card",
            ".plan-card",
            ".link-card",
            ".sidebar-card",
            ".content-shell",
            ".category-block",
            ".flow-card",
            ".search-panel",
            ".resource-group",
            ".terminal",
            ".run-copy",
            ".run-aside",
            ".hero-banner",
            ".glass-panel",
            ".jobs-section",
            ".gpu-status",
            ".chat-container",
            ".stage-container",
            ".object-manager",
            ".page-link",
            ".job-item",
            ".metric-card",
            ".category-card",
            ".product-card"
        ];

        var seen = new Set();
        selectors.forEach(function (selector) {
            document.querySelectorAll(selector).forEach(function (node) {
                seen.add(node);
            });
        });

        var nodes = Array.from(seen).filter(function (node) {
            return node && (node.childElementCount > 0 || (node.textContent || "").trim().length > 0);
        });

        if (!nodes.length) {
            return;
        }

        nodes.forEach(function (node, index) {
            node.classList.add("site-upgrade-reveal");
            node.style.setProperty("--site-upgrade-delay", Math.min(index * 28, 420) + "ms");
        });

        if (!("IntersectionObserver" in window)) {
            nodes.forEach(function (node) {
                node.classList.add("is-visible");
            });
            return;
        }

        var observer = new IntersectionObserver(function (entries, obs) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    obs.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.12,
            rootMargin: "0px 0px -8% 0px"
        });

        nodes.forEach(function (node) {
            observer.observe(node);
        });
    }

    function initUpgrade() {
        var kind = applySiteKindClass();
        var configuredPasses = getConfiguredPassCount(kind);
        var initialPasses = runPolishPasses(kind, configuredPasses);
        ensureSkipLink();
        upgradeExternalLinks();
        applyRevealAnimations();
        createPassDebugPanel(kind, initialPasses);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initUpgrade, { once: true });
    } else {
        initUpgrade();
    }
})();
