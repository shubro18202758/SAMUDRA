<script lang="ts">
  import { untrack } from 'svelte';
  import L from 'leaflet';
  import 'leaflet/dist/leaflet.css';
  import Chart from 'chart.js/auto';
  import * as THREE from 'three';

  /* ═══════ TYPES ═══════════════════════════════════════════════════════════ */
  interface TelemetryFrame {
    engine: { rpm: number; fuel_flow_kgh: number; temperature_c: number; power_kw: number; sfoc_gkwh: number };
    navigation: { speed_knots: number; heading_deg: number; latitude: number; longitude: number };
    environment: { wind_speed_kts: number; wind_direction_deg: number; sea_state: number; wave_height_m: number };
    physics: { admiralty_coefficient: number; thermal_efficiency: number; speed_ratio: number; cubic_law_power_kw: number; monsoon_resistance_pct: number; monsoon_active: boolean; pitch_deg: number; roll_deg: number; trim_fuel_penalty_pct: number };
    ais: { nmea_sentence: string; mmsi: number; cog_deg: number; current_waypoint_index: number; distance_to_waypoint_nm: number };
    ai_predictive_curve: { biological_roughness_coefficient: number; optimal_fuel_kgh: number; actual_fuel_kgh: number; penalty_pct: number; sea_surface_temp_c: number; hull_age_hours: number; curve: { speed_kts: number; optimal_fuel_kgh: number; actual_fuel_kgh: number; penalty_pct: number }[] };
    drl_optimization: { ghost_route_active: boolean; current_speed_kts: number; recommended_speed_kts: number; speed_reduction_kts: number; eta_current_s: number; eta_planned_s: number; arrival_delta_s: number; fuel_saving_kgh: number; total_fuel_saved_kg: number; mcr_load_pct: number; recommended_mcr_load_pct: number; in_mcr_band: boolean; ppo_reward: number };
    cii_segregation: { mission_state: string; cii_attained_raw: number; cii_attained_corrected: number; cii_reference: number; cii_rating_raw: string; cii_rating_corrected: string; transit_co2_tonnes: number; loiter_co2_tonnes: number; transit_fuel_tonnes: number; loiter_fuel_tonnes: number; transit_distance_nm: number; loiter_events: number; transit_events: number; elapsed_hours: number };
    ai_advisory_mode: boolean;
    sensor_integration: Record<string, any>;
    predictive_maintenance: Record<string, any>;
    hull_propulsion: Record<string, any>;
    blind_spots: Record<string, any>;
    human_ai_collaboration: Record<string, any>;
    eexi_compliance: Record<string, any>;
    data_architecture: Record<string, any>;
  }
  interface SystemAlert { id: number; severity: 'CRITICAL'|'WARNING'|'ADVISORY'|'INFO'; message: string; time: string; count: number; key: string }

  /* ═══════ NEON DESIGN TOKENS ═════════════════════════════════════════════ */
  const OB = {
    teal:'#00ffcc', cyan:'#00c8ff', amber:'#ffaa33', red:'#ff3344',
    green:'#22ff88', purple:'#b06cff', blue:'#4499ff', magenta:'#ff44aa',
    white:'#e8f0f8',
    textDim:'#3a4a5a', textSec:'#7a8fa4', textPri:'#d0dae6',
    surface0:'#060a10', surface1:'#0a1018', surface2:'#101820', surface3:'#182030',
    border:'#162030', borderHi:'#203040',
  };
  const DESIGN_SPEED_KTS = 14.5;
  const DESIGN_POWER_KW = 8500;
  const FUEL_COST_USD = 520;
  const CARBON_FACTOR = 3.114;
  const SPARK_LEN = 120;
  const FUEL_CAPACITY_TONS = 350;

  /* ═══════ HELPERS ═══════════════════════════════════════════════════════ */
  function sparkPath(d: number[], w: number, h: number): string {
    if (d.length < 2) return '';
    let mn = d[0], mx = d[0];
    for (let i = 1; i < d.length; i++) { if (d[i] < mn) mn = d[i]; if (d[i] > mx) mx = d[i]; }
    const r = mx - mn || 1;
    return d.map((v, i) => `${i === 0 ? 'M' : 'L'}${(i / (d.length - 1) * w).toFixed(1)},${(1 + (h - 2) - ((v - mn) / r) * (h - 2)).toFixed(1)}`).join(' ');
  }
  function sparkArea(d: number[], w: number, h: number): string { const l = sparkPath(d, w, h); return l ? `${l} L${w},${h} L0,${h} Z` : ''; }
  function sparkTrend(d: number[]): 'up'|'down'|'flat' {
    if (d.length < 6) return 'flat';
    const r = d.slice(-3).reduce((a, b) => a + b,0)/3, o = d.slice(-6,-3).reduce((a, b) => a + b,0)/3;
    const delta = (r - o) / (o || 1); return delta > 0.01 ? 'up' : delta < -0.01 ? 'down' : 'flat';
  }
  function gaugeArc(pct: number, r: number, cx: number, cy: number): string {
    const c = Math.max(0, Math.min(1, pct)), sA = -225, sweep = c * 270;
    const sR = sA * Math.PI / 180, eR = (sA + sweep) * Math.PI / 180;
    return `M ${(cx + r * Math.cos(sR)).toFixed(1)} ${(cy + r * Math.sin(sR)).toFixed(1)} A ${r} ${r} 0 ${sweep > 180 ? 1 : 0} 1 ${(cx + r * Math.cos(eR)).toFixed(1)} ${(cy + r * Math.sin(eR)).toFixed(1)}`;
  }
  function gColor(p: number): string { return p > 0.9 ? OB.red : p > 0.75 ? OB.amber : p > 0.5 ? OB.cyan : OB.teal; }
  const GTRACK = gaugeArc(1, 20, 24, 24);
  function fmtTime(): string { const d = new Date(); return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`; }
  function fmtElapsed(h: number): string { const s = Math.floor(h * 3600); return `${String(Math.floor(s/3600)).padStart(2,'0')}:${String(Math.floor((s%3600)/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`; }
  function beaufort(kts: number): number { const t = [1,4,7,11,17,22,28,34,41,48,56,64]; for (let i = 0; i < t.length; i++) { if (kts < t[i]) return i; } return 12; }
  function riskColor(s: number): string { return s >= 70 ? OB.red : s >= 40 ? OB.amber : s >= 20 ? OB.cyan : OB.green; }
  function riskLabel(s: number): string { return s >= 70 ? 'CRITICAL' : s >= 40 ? 'ELEVATED' : s >= 20 ? 'MODERATE' : 'LOW'; }
  function ciiColor(r: string): string { return r==='A'?OB.green:r==='B'?'#44cc88':r==='C'?OB.amber:r==='D'?'#ff7744':OB.red; }
  function froude(v_kts: number, L_m: number): number { return (v_kts * 0.5144) / Math.sqrt(9.81 * L_m); }
  function seaMarginPct(actual_kw: number, calm_kw: number): number { return calm_kw > 0 ? ((actual_kw - calm_kw) / calm_kw) * 100 : 0; }
  function fuelRange(flow_kgh: number, capacity_kg: number): number { return flow_kgh > 0 ? capacity_kg / flow_kgh : 0; }
  function enduranceDays(rangeH: number): number { return rangeH / 24; }
  function heatColor(pct: number): string { return pct > 0.9 ? '#ff2244' : pct > 0.7 ? '#ff6633' : pct > 0.5 ? '#ffaa22' : pct > 0.3 ? '#22ddaa' : '#116655'; }

  function computeRisk(t: TelemetryFrame) {
    const eng = Math.min(100, (t.drl_optimization.mcr_load_pct > 90 ? 40 : t.drl_optimization.mcr_load_pct > 75 ? 20 : 0) + (t.engine.temperature_c > 500 ? 30 : t.engine.temperature_c > 450 ? 15 : 0) + (Math.abs(t.engine.rpm - 120) > 20 ? 20 : 0));
    const nav = Math.min(100, (t.environment.sea_state >= 6 ? 50 : t.environment.sea_state >= 4 ? 25 : 0) + (t.physics.monsoon_active ? 30 : 0) + (t.environment.wave_height_m > 3 ? 20 : 0));
    const env = Math.min(100, (t.environment.wind_speed_kts > 30 ? 40 : t.environment.wind_speed_kts > 20 ? 20 : 0) + (t.environment.sea_state >= 5 ? 40 : 0) + (t.physics.monsoon_active ? 20 : 0));
    const comp = Math.min(100, (t.cii_segregation.cii_rating_corrected === 'E' ? 80 : t.cii_segregation.cii_rating_corrected === 'D' ? 50 : t.cii_segregation.cii_rating_corrected === 'C' ? 20 : 0) + (t.cii_segregation.cii_attained_corrected > t.cii_segregation.cii_reference ? 20 : 0));
    const hull = Math.min(100, (t.ai_predictive_curve.penalty_pct > 10 ? 60 : t.ai_predictive_curve.penalty_pct > 8 ? 40 : t.ai_predictive_curve.penalty_pct > 5 ? 20 : 0) + (t.ai_predictive_curve.biological_roughness_coefficient > 0.001 ? 20 : 0));
    const structural = Math.min(100, (Math.abs(t.physics.pitch_deg) > 5 ? 40 : Math.abs(t.physics.pitch_deg) > 3 ? 20 : 0) + (Math.abs(t.physics.roll_deg) > 8 ? 40 : Math.abs(t.physics.roll_deg) > 5 ? 20 : 0));
    const overall = Math.round((eng + nav + env + comp + hull + structural) / 6);
    return { eng, nav, env, comp, hull, structural, overall };
  }

  /* ═══════ REACTIVE STATE ════════════════════════════════════════════════ */
  let telemetry = $state<TelemetryFrame | null>(null);
  let connected = $state(false);
  let fps = $state(0);
  let alerts = $state<SystemAlert[]>([]);
  let activeNav = $state(0);
  let currentView = $state<'tactical'|'voyage'|'engine'|'compliance'|'settings'>('tactical');
  let aiEnabled = $state(true);
  let utcClock = $state('--:--:--');
  let missionElapsed = $state('00:00:00');
  let totalFrames = $state(0);
  let wsLatency = $state(0);
  let tickerOffset = $state(0);

  // 16 Sparkline arrays
  let sparkSOG=$state<number[]>([]),sparkFuel=$state<number[]>([]),sparkPower=$state<number[]>([]),sparkRPM=$state<number[]>([]);
  let sparkSFOC=$state<number[]>([]),sparkEta=$state<number[]>([]),sparkBRC=$state<number[]>([]),sparkMCR=$state<number[]>([]);
  let sparkCII=$state<number[]>([]),sparkWave=$state<number[]>([]),sparkReward=$state<number[]>([]),sparkTemp=$state<number[]>([]);
  let sparkFrn=$state<number[]>([]),sparkSea=$state<number[]>([]),sparkAdm=$state<number[]>([]),sparkCO2=$state<number[]>([]);

  // ── Repo UI Integration State ──
  let solasOverrideActive = $state(false);
  let imputationSens = $state(45);
  let smoothingFactor = $state(80);
  let notifCount = $state(3);

  // Segment classification data (operational modes)
  const segmentData = [
    {timeframe:'Day 1-3',mode:'TRANSIT',fuel:12.4,type:'transit'},
    {timeframe:'Day 3-5',mode:'SAR_LOITER',fuel:18.1,type:'loiter'},
    {timeframe:'Day 5-7',mode:'PATROL',fuel:15.2,type:'loiter'},
    {timeframe:'Day 7-9',mode:'TRANSIT',fuel:14.8,type:'transit'},
    {timeframe:'Day 9-10',mode:'SPRINT_INT',fuel:42.9,type:'loiter'},
    {timeframe:'Day 10-12',mode:'TRANSIT',fuel:16.5,type:'transit'},
    {timeframe:'Day 12-14',mode:'ANCHORED',fuel:2.1,type:'anchor'},
  ];

  /* ═══════ DERIVED ANALYTICS ═════════════════════════════════════════════ */
  let derived = $derived.by(() => {
    if (!telemetry) return null;
    const t = telemetry;
    const dailyFuelT = t.engine.fuel_flow_kgh * 24 / 1000;
    const co2RateKgH = t.engine.fuel_flow_kgh * CARBON_FACTOR;
    const fuelEffPct = t.ai_predictive_curve.actual_fuel_kgh > 0 ? (t.ai_predictive_curve.optimal_fuel_kgh / t.ai_predictive_curve.actual_fuel_kgh) * 100 : 100;
    const powerMarginPct = ((DESIGN_POWER_KW - t.engine.power_kw) / DESIGN_POWER_KW) * 100;
    const timeToWpH = t.navigation.speed_knots > 0.1 ? t.ais.distance_to_waypoint_nm / t.navigation.speed_knots : 0;
    const fuelToWpKg = timeToWpH * t.engine.fuel_flow_kgh;
    const bft = beaufort(t.environment.wind_speed_kts);
    const relWindDeg = ((t.environment.wind_direction_deg - t.navigation.heading_deg) + 360) % 360;
    const dailyCO2T = co2RateKgH * 24 / 1000;
    const dailyFuelCost = dailyFuelT * FUEL_COST_USD;
    const dailySavings = (t.ai_predictive_curve.actual_fuel_kgh - t.ai_predictive_curve.optimal_fuel_kgh) * 24 / 1000 * FUEL_COST_USD;
    const hullROI = t.ai_predictive_curve.penalty_pct * t.engine.fuel_flow_kgh * 0.01 * 24 / 1000 * FUEL_COST_USD;
    const risk = computeRisk(t);
    const propCoeffDev = t.physics.admiralty_coefficient > 0 ? ((t.physics.admiralty_coefficient - 385.2) / 385.2) * 100 : 0;
    const speedDef = DESIGN_SPEED_KTS - t.navigation.speed_knots;
    const totalCO2 = (t.cii_segregation.transit_co2_tonnes + t.cii_segregation.loiter_co2_tonnes) * 1000;
    const totalFuelKg = (t.cii_segregation.transit_fuel_tonnes + t.cii_segregation.loiter_fuel_tonnes) * 1000;
    const fn = froude(t.navigation.speed_knots, 91);
    const cubicCalm = DESIGN_POWER_KW * Math.pow(t.navigation.speed_knots / DESIGN_SPEED_KTS, 3);
    const seaMrg = seaMarginPct(t.engine.power_kw, cubicCalm);
    const fuelUsedKg = totalFuelKg;
    const fuelRemainKg = Math.max(0, FUEL_CAPACITY_TONS * 1000 - fuelUsedKg);
    const rangeH = fuelRange(t.engine.fuel_flow_kgh, fuelRemainKg);
    const endDays = enduranceDays(rangeH);
    const rangeNM = rangeH * t.navigation.speed_knots;
    const soxKgH = t.engine.fuel_flow_kgh * 0.025;
    const noxKgH = t.engine.fuel_flow_kgh * 0.017;
    const pmKgH = t.engine.fuel_flow_kgh * 0.005;
    const specPowerKwPerKn = t.navigation.speed_knots > 0 ? t.engine.power_kw / t.navigation.speed_knots : 0;
    const hullEffIdx = t.physics.admiralty_coefficient > 0 ? (t.physics.admiralty_coefficient / 410) * 100 : 0;
    const thermalBudgetPct = t.engine.temperature_c / 550 * 100;
    const rpmDevPct = Math.abs(t.engine.rpm - 120) / 120 * 100;
    const loadBalance = t.drl_optimization.mcr_load_pct / (t.drl_optimization.recommended_mcr_load_pct || 1) * 100;

    // ── Phase 4: 7-Gap Analytics ──
    const si = t.sensor_integration ?? {};
    const pm = t.predictive_maintenance ?? {};
    const hp = t.hull_propulsion ?? {};
    const bs = t.blind_spots ?? {};
    const hai = t.human_ai_collaboration ?? {};
    const eex = t.eexi_compliance ?? {};
    const da = t.data_architecture ?? {};

    const sensorHealthPct = si.sensors ? (Object.values(si.sensors as Record<string, any>).filter((s: any) => s?.status === 'OK' || s?.status === 'NOMINAL').length / Math.max(1, Object.keys(si.sensors).length) * 100) : 100;
    const avgRULDays = pm.components ? (Object.values(pm.components as Record<string, any>).reduce((acc: number, c: any) => acc + (c?.rul_hours ?? 0), 0) / Math.max(1, Object.keys(pm.components).length) / 24) : 999;
    const maintenanceDue = pm.scheduler?.next_due_hours ?? 999;
    const anomalyCount = pm.anomaly_detector?.active_anomalies ?? 0;
    const hullCoatingAge = hp.coating?.age_months ?? 0;
    const hullDeltaRR = hp.coating?.delta_rr_pct ?? 0;
    const batterySOC = hp.hybrid?.battery_soc_pct ?? 0;
    const propMode = hp.hybrid?.current_mode ?? 'DIESEL';
    const blindSpotRisk = bs.overall_risk_score ?? 0;
    const degradationDrift = bs.degradation?.cusum_drift ?? 0;
    const aiConfidence = hai.confidence_tier ?? 'HIGH';
    const connectivityType = hai.connectivity?.active_link ?? 'LOCAL';
    const shapTopFactor = hai.explainability?.top_factor ?? 'N/A';
    const eexiAttained = eex.eexi?.attained ?? 0;
    const eexiRequired = eex.eexi?.required ?? 0;
    const eexiCompliant = eex.eexi?.compliant ?? true;
    const ciiEnhancedRating = eex.cii_tracker?.enhanced_rating ?? t.cii_segregation.cii_rating_corrected;
    const dqiScore = da.quality?.overall_dqi ?? 1.0;
    const busMessageRate = da.bus?.messages_per_sec ?? 0;

    return {
      dailyFuelT, co2RateKgH, fuelEffPct, powerMarginPct, timeToWpH, fuelToWpKg, bft, relWindDeg,
      dailyCO2T, dailyFuelCost, dailySavings, hullROI, risk, propCoeffDev, speedDef, totalCO2, totalFuelKg,
      fn, seaMrg, fuelRemainKg, rangeH, endDays, rangeNM, soxKgH, noxKgH, pmKgH, specPowerKwPerKn,
      hullEffIdx, thermalBudgetPct, rpmDevPct, loadBalance, cubicCalm, fuelUsedKg,
      // Phase 4 gap analytics
      sensorHealthPct, avgRULDays, maintenanceDue, anomalyCount, hullCoatingAge, hullDeltaRR,
      batterySOC, propMode, blindSpotRisk, degradationDrift, aiConfidence, connectivityType,
      shapTopFactor, eexiAttained, eexiRequired, eexiCompliant, ciiEnhancedRating,
      dqiScore, busMessageRate,
    };
  });

  /* ═══════ WEBSOCKET ═══════════════════════════════════════════════════ */
  let wsRef: WebSocket | null = null;
  let framesSinceUpdate = 0, lastTick = Date.now(), alertSeq = 0;
  let reconnectAttempts = $state(0);
  const MAX_RECONNECT = 20;
  let prevMonsoon = false, prevGhost = false, prevCiiC = '', prevBioOver = false, prevTrimP = false;
  let sectionRefs: Record<string, HTMLElement | undefined> = {};
  let tsIndex = 0, lastTsUpdate = 0;

  function connectWS(): WebSocket {
    const ws = new WebSocket('ws://localhost:8000/ws/telemetry');
    wsRef = ws;
    ws.onopen = () => { connected = true; reconnectAttempts = 0; pushAlert('INFO', 'Telemetry link ESTABLISHED — all streams nominal'); };
    ws.onclose = () => { connected = false; wsRef = null; if (reconnectAttempts < MAX_RECONNECT) setTimeout(connectWS, Math.min(1000 * Math.pow(1.5, reconnectAttempts++), 15000)); };
    ws.onerror = () => { connected = false; };
    ws.onmessage = (ev: MessageEvent) => {
      framesSinceUpdate++; totalFrames++;
      const now = Date.now();
      try {
      telemetry = JSON.parse(ev.data); wsLatency = Date.now() - now;
      if (telemetry) {
        aiEnabled = telemetry.ai_advisory_mode;
        const t = telemetry;
        sparkSOG=[...sparkSOG.slice(-(SPARK_LEN-1)),t.navigation.speed_knots];
        sparkFuel=[...sparkFuel.slice(-(SPARK_LEN-1)),t.engine.fuel_flow_kgh];
        sparkPower=[...sparkPower.slice(-(SPARK_LEN-1)),t.engine.power_kw];
        sparkRPM=[...sparkRPM.slice(-(SPARK_LEN-1)),t.engine.rpm];
        sparkSFOC=[...sparkSFOC.slice(-(SPARK_LEN-1)),t.engine.sfoc_gkwh];
        sparkEta=[...sparkEta.slice(-(SPARK_LEN-1)),t.physics.thermal_efficiency*100];
        sparkBRC=[...sparkBRC.slice(-(SPARK_LEN-1)),t.ai_predictive_curve.biological_roughness_coefficient*10000];
        sparkMCR=[...sparkMCR.slice(-(SPARK_LEN-1)),t.drl_optimization.mcr_load_pct];
        sparkCII=[...sparkCII.slice(-(SPARK_LEN-1)),t.cii_segregation.cii_attained_corrected];
        sparkWave=[...sparkWave.slice(-(SPARK_LEN-1)),t.environment.wave_height_m];
        sparkReward=[...sparkReward.slice(-(SPARK_LEN-1)),t.drl_optimization.ppo_reward];
        sparkTemp=[...sparkTemp.slice(-(SPARK_LEN-1)),t.engine.temperature_c];
        sparkFrn=[...sparkFrn.slice(-(SPARK_LEN-1)),froude(t.navigation.speed_knots,91)];
        sparkSea=[...sparkSea.slice(-(SPARK_LEN-1)),t.environment.sea_state];
        sparkAdm=[...sparkAdm.slice(-(SPARK_LEN-1)),t.physics.admiralty_coefficient];
        sparkCO2=[...sparkCO2.slice(-(SPARK_LEN-1)),t.engine.fuel_flow_kgh*CARBON_FACTOR];
      }
      if (now - lastTick >= 1000) { fps = framesSinceUpdate; framesSinceUpdate = 0; lastTick = now; utcClock = new Date().toISOString().slice(11,19); if (telemetry) missionElapsed = fmtElapsed(telemetry.cii_segregation.elapsed_hours); tickerOffset = (tickerOffset + 1) % 10000; }
      checkAlerts();
      } catch (e) { console.error('[SAMUDRA] onmessage error:', e); }
    };
    return ws;
  }
  $effect(() => { const ws = connectWS(); return () => { ws.close(); wsRef = null; }; });

  function toggleAiMode() {
    aiEnabled = !aiEnabled;
    if (wsRef?.readyState === WebSocket.OPEN) wsRef.send(JSON.stringify({command:'set_ai_mode',enabled:aiEnabled}));
    pushAlert(aiEnabled ? 'INFO' : 'CRITICAL', aiEnabled ? 'AI ONLINE — PINN/DRL engaged' : 'AI OFFLINE — Baseline mode');
  }

  function pushAlert(severity: SystemAlert['severity'], message: string) {
    const time = fmtTime(), key = `${severity}:${message}`;
    const idx = alerts.findIndex(a => a.key === key);
    if (idx !== -1 && idx < 5) { const u = [...alerts]; u[idx] = {...u[idx], count: u[idx].count+1, time}; alerts = u; return; }
    alerts = [{id: ++alertSeq, severity, message, time, count: 1, key}, ...alerts].slice(0, 150);
  }

  function checkAlerts() {
    if (!telemetry) return;
    const t = telemetry;
    if (t.physics.monsoon_active && !prevMonsoon) pushAlert('CRITICAL', `MONSOON — +${t.physics.monsoon_resistance_pct.toFixed(0)}% resistance surge`);
    if (!t.physics.monsoon_active && prevMonsoon) pushAlert('INFO', 'Monsoon subsided');
    prevMonsoon = t.physics.monsoon_active;
    if (t.drl_optimization.ghost_route_active && !prevGhost) pushAlert('ADVISORY', `Ghost Route ACTIVE — target ${t.drl_optimization.recommended_speed_kts.toFixed(1)}kn`);
    if (!t.drl_optimization.ghost_route_active && prevGhost) pushAlert('INFO', 'Ghost Route disengaged');
    prevGhost = t.drl_optimization.ghost_route_active;
    const cii = t.cii_segregation.cii_rating_corrected;
    if (cii !== prevCiiC && (cii === 'D' || cii === 'E')) pushAlert('WARNING', `CII DEGRADED → ${cii}`);
    prevCiiC = cii;
    const bio = t.ai_predictive_curve.penalty_pct > 8;
    if (bio && !prevBioOver) pushAlert('WARNING', `BIO penalty ${t.ai_predictive_curve.penalty_pct.toFixed(1)}% — HULL FOUL`);
    prevBioOver = bio;
    const tp = t.physics.trim_fuel_penalty_pct > 0;
    if (tp && !prevTrimP) pushAlert('WARNING', `TRIM penalty +${t.physics.trim_fuel_penalty_pct.toFixed(1)}%`);
    if (!tp && prevTrimP) pushAlert('INFO', 'Trim nominal');
    prevTrimP = tp;
  }

  function sevIcon(s: string): string { return s==='CRITICAL'?'🔴':s==='WARNING'?'🟡':s==='ADVISORY'?'🟣':'🔵'; }

  /* ═══════ CHART 1 — FUEL CURVE (PINN) ═══════════════════════════════ */
  let c1El=$state<HTMLCanvasElement>(undefined!); let c1:Chart|undefined;
  $effect(()=>{
    if(!c1El)return;
    if(!c1){
      const ctx=c1El.getContext('2d')!;
      const g1=ctx.createLinearGradient(0,0,0,180);g1.addColorStop(0,OB.teal+'30');g1.addColorStop(1,OB.teal+'02');
      const g2=ctx.createLinearGradient(0,0,0,180);g2.addColorStop(0,OB.amber+'25');g2.addColorStop(1,OB.amber+'02');
      c1=new Chart(c1El,{type:'line',data:{labels:[],datasets:[
        {label:'Optimal',data:[],borderColor:OB.teal,backgroundColor:g1,borderWidth:1.5,pointRadius:0,fill:'origin',tension:.4},
        {label:'Actual',data:[],borderColor:OB.amber,backgroundColor:g2,borderWidth:1.5,pointRadius:0,fill:'-1',tension:.4},
      ]},options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{intersect:false,mode:'index'},
        plugins:{legend:{position:'bottom',labels:{color:OB.textSec,font:{family:"'JetBrains Mono',monospace",size:8},boxWidth:10,boxHeight:2,padding:6}},
        tooltip:{backgroundColor:OB.surface2+'f0',titleColor:OB.textPri,bodyColor:OB.textSec,borderColor:OB.border,borderWidth:1,titleFont:{size:9},bodyFont:{size:9},padding:6,cornerRadius:2}},
        scales:{x:{ticks:{color:OB.textDim,font:{size:7},maxRotation:0},grid:{color:OB.surface3+'60'},border:{color:OB.border}},y:{ticks:{color:OB.textDim,font:{size:7}},grid:{color:OB.surface3+'60'},border:{color:OB.border},beginAtZero:false}},
      },plugins:[{id:'opPt',afterDraw:(ch:any)=>{
        if(!telemetry)return;const crv=telemetry.ai_predictive_curve.curve;if(!crv.length)return;
        let ci=0,md=Infinity;crv.forEach((p:any,i:number)=>{const d=Math.abs(p.speed_kts-telemetry!.navigation.speed_knots);if(d<md){md=d;ci=i;}});
        const m=ch.getDatasetMeta(1);if(!m.data[ci])return;const x=m.data[ci].x,y=m.data[ci].y,ctx2=ch.ctx;
        ctx2.save();ctx2.strokeStyle='#ffffff18';ctx2.lineWidth=1;ctx2.setLineDash([2,3]);ctx2.beginPath();ctx2.moveTo(x,ch.scales.y.top);ctx2.lineTo(x,ch.scales.y.bottom);ctx2.stroke();
        ctx2.fillStyle='#fff';ctx2.shadowColor='#ffffff80';ctx2.shadowBlur=8;ctx2.beginPath();ctx2.arc(x,y,3,0,Math.PI*2);ctx2.fill();ctx2.restore();
      }}]});
    }
    if(telemetry&&c1){const cv=telemetry.ai_predictive_curve.curve;c1.data.labels=cv.map(p=>p.speed_kts.toFixed(1));c1.data.datasets[0].data=cv.map(p=>p.optimal_fuel_kgh);c1.data.datasets[1].data=cv.map(p=>p.actual_fuel_kgh);c1.update('none');}
  });

  /* ═══════ CHART 2 — REAL-TIME TELEMETRY ═════════════════════════════ */
  let c2El=$state<HTMLCanvasElement>(undefined!); let c2:Chart|undefined;
  $effect(()=>{
    if(!c2El)return;
    if(!c2){c2=new Chart(c2El,{type:'line',data:{labels:[],datasets:[
      {label:'SOG kn',data:[],borderColor:OB.teal,borderWidth:1.2,pointRadius:0,tension:.3,yAxisID:'y'},
      {label:'Fuel kg/h',data:[],borderColor:OB.amber,borderWidth:1.2,pointRadius:0,tension:.3,yAxisID:'y1'},
      {label:'Power/100kW',data:[],borderColor:OB.purple,borderWidth:1.2,pointRadius:0,tension:.3,yAxisID:'y1'},
    ]},options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{intersect:false,mode:'index'},
      plugins:{legend:{position:'bottom',labels:{color:OB.textSec,font:{size:8},boxWidth:10,boxHeight:2,padding:6}},tooltip:{backgroundColor:OB.surface2+'f0',titleColor:OB.textPri,bodyColor:OB.textSec,borderColor:OB.border,borderWidth:1,padding:6,cornerRadius:2}},
      scales:{x:{display:false},y:{position:'left',ticks:{color:OB.textDim,font:{size:7}},grid:{color:OB.surface3+'40'},border:{color:OB.border}},
      y1:{position:'right',ticks:{color:OB.textDim,font:{size:7}},grid:{drawOnChartArea:false},border:{color:OB.border}}},
    }});}
    if(telemetry&&c2){const n=Date.now();if(n-lastTsUpdate<500)return;lastTsUpdate=n;tsIndex++;
      if((c2.data.labels as string[]).length>=120){(c2.data.labels as string[]).shift();c2.data.datasets.forEach(ds=>(ds.data as number[]).shift());}
      (c2.data.labels as string[]).push(`${tsIndex}`);(c2.data.datasets[0].data as number[]).push(telemetry.navigation.speed_knots);(c2.data.datasets[1].data as number[]).push(telemetry.engine.fuel_flow_kgh);(c2.data.datasets[2].data as number[]).push(telemetry.engine.power_kw/100);c2.update('none');}
  });

  /* ═══════ CHART 3 — SPEED-POWER ENVELOPE ════════════════════════════ */
  let c3El=$state<HTMLCanvasElement>(undefined!); let c3:Chart|undefined;
  $effect(()=>{
    if(!c3El)return;
    if(!c3){const spds:number[]=[],cpw:number[]=[];for(let v=5;v<=20;v+=0.5){spds.push(v);cpw.push(DESIGN_POWER_KW*Math.pow(v/DESIGN_SPEED_KTS,3));}
      c3=new Chart(c3El,{type:'line',data:{labels:spds.map(s=>s.toFixed(1)),datasets:[
        {label:'P∝V³ Law',data:cpw,borderColor:OB.cyan+'80',borderWidth:1.5,pointRadius:0,borderDash:[3,3],tension:.4,fill:false},
        {label:'Actual',data:cpw.map(()=>null as any),borderColor:OB.amber,borderWidth:0,pointRadius:0,fill:false},
      ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
        plugins:{legend:{position:'bottom',labels:{color:OB.textSec,font:{size:8},boxWidth:10,boxHeight:2,padding:6}},tooltip:{backgroundColor:OB.surface2+'f0',titleColor:OB.textPri,bodyColor:OB.textSec,borderColor:OB.border,borderWidth:1,padding:6,cornerRadius:2}},
        scales:{x:{ticks:{color:OB.textDim,font:{size:7},maxRotation:0,maxTicksLimit:8},grid:{color:OB.surface3+'40'},border:{color:OB.border}},y:{ticks:{color:OB.textDim,font:{size:7}},grid:{color:OB.surface3+'40'},border:{color:OB.border}}},
      },plugins:[{id:'opPt',afterDraw:(ch:any)=>{
        if(!telemetry)return;const xS=ch.scales.x,yS=ch.scales.y,spd2=telemetry.navigation.speed_knots,pwr=telemetry.engine.power_kw;
        const lb=ch.data.labels as string[];let ci2=0,md2=Infinity;lb.forEach((l:string,i:number)=>{const d=Math.abs(parseFloat(l)-spd2);if(d<md2){md2=d;ci2=i;}});
        const meta=ch.getDatasetMeta(0);if(!meta.data[ci2])return;const px=meta.data[ci2].x,py=yS.getPixelForValue(pwr),ctx3=ch.ctx;
        ctx3.save();ctx3.fillStyle=OB.amber;ctx3.shadowColor=OB.amber+'80';ctx3.shadowBlur=8;ctx3.beginPath();ctx3.arc(px,py,4,0,Math.PI*2);ctx3.fill();
        let di=0,dm=Infinity;lb.forEach((l:string,i:number)=>{const d=Math.abs(parseFloat(l)-DESIGN_SPEED_KTS);if(d<dm){dm=d;di=i;}});
        const dp=meta.data[di]?.x,dpy=yS.getPixelForValue(DESIGN_POWER_KW);
        if(dp){ctx3.fillStyle=OB.green;ctx3.shadowColor=OB.green+'80';ctx3.beginPath();ctx3.arc(dp,dpy,3.5,0,Math.PI*2);ctx3.fill();}ctx3.restore();
      }}]});
    }
  });

  /* ═══════ CHART 4 — EFFICIENCY TREND ════════════════════════════════ */
  let c4El=$state<HTMLCanvasElement>(undefined!); let c4:Chart|undefined; let c4Idx=0;
  $effect(()=>{
    if(!c4El)return;
    if(!c4){
      const ctx=c4El.getContext('2d')!;
      const g=ctx.createLinearGradient(0,0,0,150);g.addColorStop(0,OB.green+'30');g.addColorStop(1,OB.green+'02');
      c4=new Chart(c4El,{type:'line',data:{labels:[],datasets:[
        {label:'Fuel Eff %',data:[],borderColor:OB.green,backgroundColor:g,borderWidth:1.2,pointRadius:0,tension:.3,fill:'origin'},
        {label:'Thermal η%',data:[],borderColor:OB.cyan,borderWidth:1.2,pointRadius:0,tension:.3,fill:false},
      ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
        plugins:{legend:{position:'bottom',labels:{color:OB.textSec,font:{size:8},boxWidth:10,boxHeight:2,padding:6}}},
        scales:{x:{display:false},y:{min:60,max:110,ticks:{color:OB.textDim,font:{size:7}},grid:{color:OB.surface3+'40'},border:{color:OB.border}}},
      }});
    }
    if(telemetry&&c4&&derived){const n=Date.now();if(n-lastTsUpdate<600)return;c4Idx++;
      if((c4.data.labels as string[]).length>=100){(c4.data.labels as string[]).shift();c4.data.datasets.forEach(ds=>(ds.data as number[]).shift());}
      (c4.data.labels as string[]).push(`${c4Idx}`);
      (c4.data.datasets[0].data as number[]).push(derived.fuelEffPct);
      (c4.data.datasets[1].data as number[]).push(telemetry.physics.thermal_efficiency*100);
      c4.update('none');
    }
  });

  /* ═══════ CHART 5 — ENVIRONMENTAL ═══════════════════════════════════ */
  let c5El=$state<HTMLCanvasElement>(undefined!); let c5:Chart|undefined; let c5Idx=0;
  $effect(()=>{
    if(!c5El)return;
    if(!c5){c5=new Chart(c5El,{type:'line',data:{labels:[],datasets:[
      {label:'Wind kts',data:[],borderColor:OB.cyan,borderWidth:1.2,pointRadius:0,tension:.3,yAxisID:'y'},
      {label:'Wave m',data:[],borderColor:OB.blue,borderWidth:1.2,pointRadius:0,tension:.3,yAxisID:'y1'},
      {label:'Sea State',data:[],borderColor:OB.purple,borderWidth:1,pointRadius:0,tension:.3,yAxisID:'y1',borderDash:[2,2]},
    ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{position:'bottom',labels:{color:OB.textSec,font:{size:8},boxWidth:10,boxHeight:2,padding:6}}},
      scales:{x:{display:false},y:{position:'left',ticks:{color:OB.textDim,font:{size:7}},grid:{color:OB.surface3+'40'},border:{color:OB.border}},
      y1:{position:'right',ticks:{color:OB.textDim,font:{size:7}},grid:{drawOnChartArea:false},border:{color:OB.border}}},
    }});}
    if(telemetry&&c5){c5Idx++;
      if((c5.data.labels as string[]).length>=100){(c5.data.labels as string[]).shift();c5.data.datasets.forEach(ds=>(ds.data as number[]).shift());}
      (c5.data.labels as string[]).push(`${c5Idx}`);
      (c5.data.datasets[0].data as number[]).push(telemetry.environment.wind_speed_kts);
      (c5.data.datasets[1].data as number[]).push(telemetry.environment.wave_height_m);
      (c5.data.datasets[2].data as number[]).push(telemetry.environment.sea_state);c5.update('none');
    }
  });

  /* ═══════ CHART 6 — LSTM 24HR BAR (Engine) ══════════════════════════ */
  let c6El=$state<HTMLCanvasElement>(undefined!); let c6:Chart|undefined;
  $effect(()=>{
    if(!c6El)return;
    // Build 24 hourly bins from lstmHistory
    const h=lstmHistory;
    const bars:number[]=[];const labels:string[]=[];
    const bsz=Math.max(1,Math.floor(h.length/24));
    for(let i=0;i<24;i++){
      labels.push(`${String(i).padStart(2,'0')}:00`);
      const sl=h.slice(i*bsz,(i+1)*bsz);
      bars.push(sl.length?sl.reduce((a:number,b:number)=>a+b,0)/sl.length:Math.random()*0.3+0.1);
    }
    const bgCols=bars.map(v=>v>lstmThreshold*0.8?OB.amber+'aa':OB.cyan+'55');
    const bdCols=bars.map(v=>v>lstmThreshold*0.8?OB.amber:OB.cyan);
    if(!c6){
      c6=new Chart(c6El,{type:'bar',data:{labels,datasets:[{label:'MSE',data:bars,backgroundColor:bgCols,borderColor:bdCols,borderWidth:1,borderRadius:2}]},
        options:{responsive:true,maintainAspectRatio:false,animation:false,
          plugins:{legend:{display:false},tooltip:{backgroundColor:OB.surface2+'f0',titleColor:OB.textPri,bodyColor:OB.textSec,borderColor:OB.border,borderWidth:1,padding:6,cornerRadius:2}},
          scales:{x:{ticks:{color:OB.textDim,font:{size:6},maxRotation:0,maxTicksLimit:12},grid:{display:false},border:{color:OB.border}},
            y:{min:0,max:1.2,ticks:{color:OB.textDim,font:{size:7}},grid:{color:OB.surface3+'40'},border:{color:OB.border}}},
        },plugins:[{id:'thrLine',afterDraw:(ch:any)=>{
          const yS=ch.scales.y,ctx2=ch.ctx,yP=yS.getPixelForValue(lstmThreshold);
          ctx2.save();ctx2.strokeStyle=OB.red;ctx2.lineWidth=1;ctx2.setLineDash([4,4]);ctx2.beginPath();ctx2.moveTo(ch.chartArea.left,yP);ctx2.lineTo(ch.chartArea.right,yP);ctx2.stroke();ctx2.restore();
        }}]});
    } else {c6.data.labels=labels;c6.data.datasets[0].data=bars;(c6.data.datasets[0] as any).backgroundColor=bgCols;(c6.data.datasets[0] as any).borderColor=bdCols;c6.update('none');}
  });

  /* ═══════ CHART 7 — DBSCAN SCATTER (Compliance) ═════════════════════ */
  let c7El=$state<HTMLCanvasElement>(undefined!); let c7:Chart|undefined;
  $effect(()=>{
    if(!c7El)return;
    if(!c7){
      // Generate sample clusters: Transit (high speed, high load) + Patrol/Loiter (low speed, low load)
      const transit=Array.from({length:40},()=>({x:12+Math.random()*8,y:50+Math.random()*40}));
      const patrol=Array.from({length:30},()=>({x:2+Math.random()*6,y:20+Math.random()*25}));
      c7=new Chart(c7El,{type:'scatter',data:{datasets:[
        {label:'Transit',data:transit,backgroundColor:OB.cyan+'88',borderColor:OB.cyan,pointRadius:3.5,pointHoverRadius:5},
        {label:'Patrol/Loiter',data:patrol,backgroundColor:OB.amber+'88',borderColor:OB.amber,pointRadius:3.5,pointHoverRadius:5},
      ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
        plugins:{legend:{position:'bottom',labels:{color:OB.textSec,font:{size:8},boxWidth:10,boxHeight:2,padding:6}},
          tooltip:{backgroundColor:OB.surface2+'f0',titleColor:OB.textPri,bodyColor:OB.textSec,borderColor:OB.border,borderWidth:1,padding:6,cornerRadius:2}},
        scales:{x:{title:{display:true,text:'SOG (kt)',color:OB.textDim,font:{size:8}},ticks:{color:OB.textDim,font:{size:7}},grid:{color:OB.surface3+'40'},border:{color:OB.border},min:0,max:25},
          y:{title:{display:true,text:'Engine Load (%)',color:OB.textDim,font:{size:8}},ticks:{color:OB.textDim,font:{size:7}},grid:{color:OB.surface3+'40'},border:{color:OB.border},min:0,max:100}},
      }});
    }
    // Update latest transit point with live data
    if(telemetry&&c7){
      const td=c7.data.datasets[0].data as {x:number,y:number}[];
      if(td.length>0){td[td.length-1]={x:telemetry.navigation.speed_knots,y:telemetry.drl_optimization.mcr_load_pct};c7.update('none');}
    }
  });

  /* ═══════ LEAFLET MAP — ENHANCED TACTICAL DISPLAY ═══════════════════ */
  let mapEl=$state<HTMLDivElement>(undefined!); let lMap:L.Map|undefined; let vMark:L.Marker|undefined; let hdgLine:L.Polyline|undefined; let trackLine:L.Polyline|undefined; let trackC:[number,number][]=[];
  let rangeRings:L.Circle[]=[]; let bearingLines:L.Polyline[]=[]; let windArrow:L.Polyline|undefined; let wpLabels:L.Marker[]=[]; let routeCorridor:L.Polyline|undefined;
  const WPS:([number,number])[]= [[18.922,72.836],[16.980,73.100],[15.410,73.780],[14.800,74.050],[12.870,74.810],[9.970,76.260],[10.570,72.640],[8.280,73.040],[12.500,68.000],[15.700,71.000]];
  const WP_NAMES=['MUMBAI','RATNAGIRI','GOA','KARWAR','MANGALORE','KOCHI','LAKSHADWEEP','MINICOY','OPEN SEA-1','OPEN SEA-2'];
  function shipIcon(hdg:number,spd:number):L.DivIcon{
    const c=spd>12?'#22ff88':spd>8?'#ffaa33':'#ff3344';
    return L.divIcon({className:'',iconSize:[28,28],iconAnchor:[14,14],
      html:`<svg width="28" height="28" viewBox="-14 -14 28 28" style="transform:rotate(${hdg}deg)"><defs><filter id="sg"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><polygon points="0,-12 4,8 0,5 -4,8" fill="${c}" stroke="#00ffcc" stroke-width="0.8" opacity="0.9" filter="url(#sg)"/><circle cx="0" cy="0" r="1.5" fill="#fff" opacity="0.7"/></svg>`});
  }
  $effect(()=>{
    if(!mapEl||lMap)return;
    lMap=L.map(mapEl,{zoomControl:false}).setView([13.0,72.5],6);
    L.control.zoom({position:'topright'}).addTo(lMap);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{attribution:'&copy;CartoDB',subdomains:'abcd',maxZoom:19}).addTo(lMap);
    // Route corridor — wide translucent buffer
    routeCorridor=L.polyline([...WPS,WPS[0]],{color:OB.cyan,weight:14,opacity:0.05,lineCap:'round',lineJoin:'round'}).addTo(lMap);
    L.polyline([...WPS,WPS[0]],{color:OB.cyan,weight:1.2,dashArray:'6,10',opacity:.4}).addTo(lMap);
    // Enhanced waypoints with named labels + approach zones
    WPS.forEach((wp,i)=>{
      L.circleMarker(wp,{radius:3.5,color:OB.cyan,fillColor:OB.cyan,fillOpacity:.6,weight:1.2}).bindTooltip(`WP${i} — ${WP_NAMES[i]}`,{permanent:false,direction:'top',className:'wp-tt'}).addTo(lMap!);
      L.circle(wp,{radius:3000,color:OB.cyan,fillColor:OB.cyan,fillOpacity:0.03,weight:0.5,opacity:0.15}).addTo(lMap!);
      L.circle(wp,{radius:800,color:OB.teal,fillColor:OB.teal,fillOpacity:0.06,weight:0.8,opacity:0.25}).addTo(lMap!);
      const lbl=L.marker(wp,{icon:L.divIcon({className:'wp-label',html:`<span>${WP_NAMES[i]}</span>`,iconSize:[64,14],iconAnchor:[32,-8]})}).addTo(lMap!);
      wpLabels.push(lbl);
    });
    // Vessel — directional SVG ship icon (replaces circle marker)
    vMark=L.marker(WPS[0],{icon:shipIcon(0,0),zIndexOffset:1000}).addTo(lMap);
    hdgLine=L.polyline([],{color:OB.amber,weight:2,opacity:.85,dashArray:'4,6'}).addTo(lMap);
    trackLine=L.polyline([],{color:OB.amber,weight:1.5,opacity:.35}).addTo(lMap);
    // Range rings — 1nm, 3nm, 5nm
    const nmToM=1852;
    [1,3,5].forEach(nm=>{
      const ring=L.circle(WPS[0],{radius:nm*nmToM,color:OB.cyan,fillColor:'transparent',fillOpacity:0,weight:0.6,opacity:0.2,dashArray:'4,8'}).addTo(lMap!);
      rangeRings.push(ring);
    });
    // Bearing compass lines — 8 cardinal/intercardinal directions
    for(let b=0;b<360;b+=45){
      const br=b*Math.PI/180,ext=0.12;
      const bl=L.polyline([WPS[0],[WPS[0][0]+Math.cos(br)*ext,WPS[0][1]+Math.sin(br)*ext]],{color:OB.cyan,weight:0.4,opacity:0.12,dashArray:'2,6'}).addTo(lMap);
      bearingLines.push(bl);
    }
    // Wind vector arrow
    windArrow=L.polyline([],{color:OB.amber,weight:2.5,opacity:0.4,dashArray:'2,4'}).addTo(lMap);
    // DRL Ghost Route — thicker, more visible
    ghostLine=L.polyline([],{color:'#b06cff',weight:3,opacity:.55,dashArray:'10,8'}).addTo(lMap);
    ghostMarker=L.circleMarker(WPS[0],{radius:4,color:'#b06cff',fillColor:'#b06cff',fillOpacity:.5,weight:1.5}).addTo(lMap);
  });
  $effect(()=>{
    if(!telemetry||!vMark||!trackLine||!hdgLine||!lMap)return;
    const p:[number,number]=[telemetry.navigation.latitude,telemetry.navigation.longitude];
    // Vessel icon — rotated by heading, colored by speed
    vMark.setLatLng(p);vMark.setIcon(shipIcon(telemetry.navigation.heading_deg,telemetry.navigation.speed_knots));
    const h=telemetry.navigation.heading_deg,sc=.1+telemetry.navigation.speed_knots*.006,hr=h*Math.PI/180,cL=Math.cos(p[0]*Math.PI/180);
    hdgLine.setLatLngs([p,[p[0]+Math.cos(hr)*sc,p[1]+Math.sin(hr)*sc/(cL||1)]]);
    trackC.push(p);if(trackC.length>2500)trackC=trackC.slice(-2000);trackLine.setLatLngs(trackC);
    // Range rings follow vessel
    rangeRings.forEach(ring=>{ring.setLatLng(p);});
    // Bearing lines follow vessel
    bearingLines.forEach((bl,i)=>{const b=i*45*Math.PI/180,ext=0.12;
      bl.setLatLngs([p,[p[0]+Math.cos(b)*ext,p[1]+Math.sin(b)*ext/(cL||1)]]);});
    // Wind vector from vessel position
    if(windArrow){const wd=telemetry.environment.wind_direction_deg*Math.PI/180,ws=telemetry.environment.wind_speed_kts*0.002;
      windArrow.setLatLngs([p,[p[0]+Math.cos(wd)*ws,p[1]+Math.sin(wd)*ws/(cL||1)]]);}
    // Ghost route update
    if(ghostLine&&ghostMarker){
      if(telemetry.drl_optimization.ghost_route_active){
        const gOff=0.012+Math.sin(Date.now()*0.0008)*0.004;
        const gp:[number,number]=[p[0]+gOff,p[1]-gOff*0.8];
        ghostMarker.setLatLng(gp);ghostMarker.setStyle({fillOpacity:.7,opacity:1});
        const nwi=Math.min(telemetry.ais.current_waypoint_index+1,WPS.length-1);
        const nw=WPS[nwi];
        ghostLine.setLatLngs([p,gp,[(gp[0]+nw[0])/2+gOff*0.5,(gp[1]+nw[1])/2-gOff*0.3],nw]);ghostLine.setStyle({opacity:.55});
      } else {ghostLine.setLatLngs([]);ghostMarker.setStyle({fillOpacity:0,opacity:0});}
    }
  });

  /* ═══════ THREE.JS 3D HULL — DIGITAL TWIN v5 ═══════════════════════ */
  function buildHull():THREE.BufferGeometry{
    // 52 stations × 32 frames: bulbous bow, transom stern, hull flare, deck sheer
    const ST=52,FR=32,HL=3.8,HB=0.65,HD=0.42;const vs:number[]=[],ix:number[]=[];
    for(let i=0;i<=ST;i++){const t=i/ST,z=-HL/2+t*HL;
      const bowT=t<0.12?Math.pow(t/0.12,0.55):1;const sternT=t>0.82?Math.pow((1-t)/0.18,0.45):1;
      const midB=Math.pow(Math.sin(t*Math.PI),0.38);const beam=HB*midB*bowT*sternT;
      const depth=HD*Math.pow(Math.sin(t*Math.PI),0.3)*(0.85+0.15*Math.pow(Math.sin(t*Math.PI),0.5));
      const flare=t<0.25?1.12-t*0.4:t>0.8?1.05:1.0;
      const bulb=t<0.06?Math.sin(t/0.06*Math.PI)*0.14:0;
      for(let j=0;j<=FR;j++){const a=(j/FR)*Math.PI;
        vs.push(beam*flare*Math.cos(a)+bulb*Math.cos(a*1.5),-depth*Math.sin(a)*(0.92+0.08*Math.cos(a)),z);}}
    for(let i=0;i<ST;i++)for(let j=0;j<FR;j++){const a=i*(FR+1)+j,c=(i+1)*(FR+1)+j;ix.push(a,a+1,c,a+1,c+1,c);}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vs,3));g.setIndex(ix);g.computeVertexNormals();return g;
  }
  function buildDeck(hGeo:THREE.BufferGeometry):THREE.BufferGeometry{
    const pos=hGeo.getAttribute('position');const ST=52,FR=32,dv:number[]=[],di:number[]=[];
    for(let i=0;i<=ST;i++){const b=i*(FR+1);dv.push(pos.getX(b),0.01,pos.getZ(b),0,0.01,pos.getZ(b),pos.getX(b+FR),0.01,pos.getZ(b));}
    for(let i=0;i<ST;i++){const b=i*3;di.push(b,b+1,b+3,b+1,b+4,b+3,b+1,b+2,b+4,b+2,b+5,b+4);}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(dv,3));g.setIndex(di);g.computeVertexNormals();return g;
  }
  let hullEl=$state<HTMLCanvasElement>(undefined!);let threeR:THREE.WebGLRenderer|undefined;let hullGroup:THREE.Group|undefined;
  let hullWireMat:THREE.LineBasicMaterial|undefined;let hullSolidMat:THREE.MeshStandardMaterial|undefined;let seaGeo:THREE.PlaneGeometry|undefined;
  let hTP=0,hTR=0,hCP=0,hCR=0,hTW=false,hSpd=0;
  const HC=new THREE.Color(0x00c8ff),HA=new THREE.Color(0xff9933),HCS=new THREE.Color(0x07131f),HAS=new THREE.Color(0x1a0e05);
  $effect(()=>{
    if(!hullEl||threeR)return;
    const sc=new THREE.Scene();sc.fog=new THREE.FogExp2(0x040810,0.055);
    const cam=new THREE.PerspectiveCamera(36,hullEl.clientWidth/hullEl.clientHeight,0.1,120);cam.position.set(6,4,8);cam.lookAt(0,-0.1,0);
    // Hemisphere + ambient + dual directional for dramatic ocean lighting
    sc.add(new THREE.HemisphereLight(0x1a3a5c,0x020408,0.5));sc.add(new THREE.AmbientLight(0x00c8ff,0.2));
    const dl=new THREE.DirectionalLight(0xccddff,0.5);dl.position.set(8,12,6);sc.add(dl);
    const dl2=new THREE.DirectionalLight(0x003355,0.2);dl2.position.set(-5,3,-8);sc.add(dl2);
    // ── HULL — solid body + wireframe overlay for digital twin aesthetic ──
    const hGeo=buildHull();
    hullSolidMat=new THREE.MeshStandardMaterial({color:0x07131f,metalness:0.35,roughness:0.55,transparent:true,opacity:0.75,side:THREE.DoubleSide});
    const solidH=new THREE.Mesh(hGeo,hullSolidMat);
    hullWireMat=new THREE.LineBasicMaterial({color:0x00c8ff,transparent:true,opacity:0.7});
    const wireH=new THREE.LineSegments(new THREE.WireframeGeometry(hGeo),hullWireMat);
    hullGroup=new THREE.Group();hullGroup.add(solidH);hullGroup.add(wireH);
    // ── DECK PLATE ──
    const dGeo=buildDeck(hGeo);
    hullGroup.add(new THREE.Mesh(dGeo,new THREE.MeshStandardMaterial({color:0x0a1a2a,metalness:0.3,roughness:0.6,transparent:true,opacity:0.55,side:THREE.DoubleSide})));
    hullGroup.add(new THREE.LineSegments(new THREE.WireframeGeometry(dGeo),new THREE.LineBasicMaterial({color:0x00ffcc,transparent:true,opacity:0.25})));
    // ── SUPERSTRUCTURE — bridge block, funnel, mast, radar ──
    const sMat=new THREE.MeshStandardMaterial({color:0x0a1520,metalness:0.3,roughness:0.7,transparent:true,opacity:0.6});
    const brGeo=new THREE.BoxGeometry(0.42,0.52,0.7);const br=new THREE.Mesh(brGeo,sMat);br.position.set(0,0.3,-1.05);hullGroup.add(br);
    const brEdge=new THREE.LineSegments(new THREE.EdgesGeometry(brGeo),new THREE.LineBasicMaterial({color:0x00c8ff,transparent:true,opacity:0.55}));brEdge.position.copy(br.position);hullGroup.add(brEdge);
    // Bridge windows
    const winM=new THREE.Mesh(new THREE.BoxGeometry(0.44,0.08,0.02),new THREE.MeshBasicMaterial({color:0x00ffcc,transparent:true,opacity:0.35}));winM.position.set(0,0.48,-0.69);hullGroup.add(winM);
    // Funnel
    const fnGeo=new THREE.CylinderGeometry(0.06,0.09,0.35,8);const fn=new THREE.Mesh(fnGeo,sMat.clone());fn.position.set(0,0.78,-1.15);hullGroup.add(fn);
    const fnEdge=new THREE.LineSegments(new THREE.EdgesGeometry(fnGeo),new THREE.LineBasicMaterial({color:0x00c8ff,transparent:true,opacity:0.4}));fnEdge.position.copy(fn.position);hullGroup.add(fnEdge);
    // Mast
    const mst=new THREE.Mesh(new THREE.CylinderGeometry(0.012,0.012,0.8,4),new THREE.MeshBasicMaterial({color:0x00c8ff,transparent:true,opacity:0.5}));mst.position.set(0,0.45,0.9);hullGroup.add(mst);
    // Rotating radar scanner
    const radar=new THREE.Mesh(new THREE.BoxGeometry(0.4,0.015,0.03),new THREE.MeshBasicMaterial({color:0x00ffcc,transparent:true,opacity:0.5}));radar.position.set(0,0.85,0.9);hullGroup.add(radar);
    // ── NAVIGATION LIGHT SPHERES (COLREG compliant) ──
    const nlG=new THREE.SphereGeometry(0.035,12,8);
    const mkNL=(c:number,e:number,p:[number,number,number])=>{
      const m=new THREE.Mesh(nlG,new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:0.9}));m.position.set(...p);hullGroup!.add(m);
      const pl=new THREE.PointLight(c,e,2.5);pl.position.set(...p);hullGroup!.add(pl);return m;};
    const nlP=mkNL(0xff2233,0.4,[-0.55,0.12,0.2]);const nlS=mkNL(0x22ff66,0.4,[0.55,0.12,0.2]);
    const nlM=mkNL(0xffffff,0.5,[0,0.88,0.9]);mkNL(0xffffff,0.3,[0,0.15,-1.85]);
    // ── PROPELLER DISC — speed-responsive spin ──
    const propDisc=new THREE.Mesh(new THREE.CircleGeometry(0.15,16),new THREE.MeshBasicMaterial({color:0x00c8ff,transparent:true,opacity:0.2,side:THREE.DoubleSide}));
    propDisc.position.set(0,-0.12,-1.9);propDisc.rotation.y=Math.PI/2;hullGroup.add(propDisc);
    // ── DRAFT MARKS ──
    const dmM=new THREE.LineBasicMaterial({color:0xffaa33,transparent:true,opacity:0.4});
    for(let d=1;d<=4;d++){const y=-d*0.09;
      hullGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(-0.68,y,1.2),new THREE.Vector3(-0.68,y,1.35)]),dmM));
      hullGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0.68,y,1.2),new THREE.Vector3(0.68,y,1.35)]),dmM));}
    sc.add(hullGroup);
    // ── WATERLINE RING ──
    const wl=new THREE.Mesh(new THREE.RingGeometry(0.54,0.57,80),new THREE.MeshBasicMaterial({color:0x00ffcc,transparent:true,opacity:0.12,side:THREE.DoubleSide}));wl.rotation.x=-Math.PI/2;wl.position.y=0.005;wl.scale.set(6.5,6.5,1);sc.add(wl);
    // ── SEA SURFACE — higher res with 4-component wave ──
    seaGeo=new THREE.PlaneGeometry(20,20,60,60);
    const seaM=new THREE.Mesh(seaGeo,new THREE.MeshPhongMaterial({color:0x051525,transparent:true,opacity:0.25,shininess:100,side:THREE.DoubleSide}));seaM.rotation.x=-Math.PI/2;seaM.position.y=0.01;sc.add(seaM);
    // Foam ring at waterline
    const foam=new THREE.Mesh(new THREE.RingGeometry(1.6,2.0,64),new THREE.MeshBasicMaterial({color:0xaaddff,transparent:true,opacity:0.04,side:THREE.DoubleSide}));foam.rotation.x=-Math.PI/2;foam.position.y=0.02;foam.scale.set(2,1.2,1);sc.add(foam);
    // Grid
    const gh=new THREE.GridHelper(20,40,0x0c1520,0x0c1520);gh.position.y=-0.6;(gh.material as THREE.Material).opacity=0.15;(gh.material as THREE.Material).transparent=true;sc.add(gh);
    // ── BOW WAVE — V-shaped, speed-responsive ──
    const bwV:number[]=[],bwI:number[]=[];const BWS=20;
    for(let i=0;i<=BWS;i++){const t=i/BWS,z=1.85-t*3.5,sp=t*1.2;bwV.push(-sp,0.02,z,0,0.02,z+0.15,sp,0.02,z);}
    for(let i=0;i<BWS;i++){const b=i*3;bwI.push(b,b+1,b+3,b+1,b+4,b+3,b+1,b+2,b+4,b+2,b+5,b+4);}
    const bowWaveGeo=new THREE.BufferGeometry();bowWaveGeo.setAttribute('position',new THREE.Float32BufferAttribute(bwV,3));bowWaveGeo.setIndex(bwI);
    const bwMat=new THREE.MeshBasicMaterial({color:0x88ccff,transparent:true,opacity:0.06,side:THREE.DoubleSide});
    const bowWaveM=new THREE.Mesh(bowWaveGeo,bwMat);sc.add(bowWaveM);
    // ── WAKE PARTICLES — 400 dense trail ──
    const wkGeo=new THREE.BufferGeometry();const wkP:number[]=[];
    for(let i=0;i<400;i++){const t=Math.random(),sp=t*0.8;wkP.push((Math.random()-0.5)*sp,Math.random()*-0.03,-1.9-t*5.5);}
    wkGeo.setAttribute('position',new THREE.Float32BufferAttribute(wkP,3));
    const wkPts=new THREE.Points(wkGeo,new THREE.PointsMaterial({color:0x66ddff,size:0.025,transparent:true,opacity:0.35,sizeAttenuation:true}));sc.add(wkPts);
    // ── BOW SPRAY PARTICLES ──
    const spGeo=new THREE.BufferGeometry();const spP:number[]=[];
    for(let i=0;i<80;i++)spP.push((Math.random()-0.5)*0.3,Math.random()*0.2,1.7+Math.random()*0.5);
    spGeo.setAttribute('position',new THREE.Float32BufferAttribute(spP,3));
    const spMat=new THREE.PointsMaterial({color:0xccffff,size:0.018,transparent:true,opacity:0.25});
    const spPts=new THREE.Points(spGeo,spMat);sc.add(spPts);
    // ── RENDERER — ACES filmic tone mapping ──
    const r=new THREE.WebGLRenderer({canvas:hullEl,antialias:true,alpha:true});r.setPixelRatio(Math.min(window.devicePixelRatio,2));r.setSize(hullEl.clientWidth,hullEl.clientHeight);
    r.setClearColor(0x040810,1);r.toneMapping=THREE.ACESFilmicToneMapping;r.toneMappingExposure=1.1;threeR=r;
    let run=true;const t0=performance.now();let camA=0;
    (function anim(){if(!run)return;requestAnimationFrame(anim);const tn=(performance.now()-t0)*0.001;hCP+=(hTP-hCP)*0.08;hCR+=(hTR-hCR)*0.08;
      // Camera auto-orbit
      camA+=0.002;const oR=9,oH=3.8;cam.position.set(Math.cos(camA)*oR,oH+Math.sin(tn*0.3)*0.3,Math.sin(camA)*oR);cam.lookAt(0,-0.1,0);
      // Hull motion from telemetry pitch/roll
      if(hullGroup){hullGroup.rotation.x=hCP+Math.sin(tn*0.6)*0.028;hullGroup.rotation.z=hCR+Math.sin(tn*0.4)*0.02;hullGroup.rotation.y=Math.sin(tn*0.15)*0.08;hullGroup.position.y=Math.sin(tn*0.8)*0.045;}
      // Trim warning color lerp — wireframe + solid body
      if(hullWireMat)hullWireMat.color.lerp(hTW?HA:HC,0.04);
      if(hullSolidMat)hullSolidMat.color.lerp(hTW?HAS:HCS,0.04);
      // Radar spin
      radar.rotation.y=tn*2.5;
      // Propeller speed-responsive spin
      propDisc.rotation.x=tn*(3+hSpd*0.3);
      // Nav light pulse
      const pulse=0.7+Math.sin(tn*3)*0.3;
      (nlP.material as THREE.MeshBasicMaterial).opacity=pulse;(nlS.material as THREE.MeshBasicMaterial).opacity=pulse;
      (nlM.material as THREE.MeshBasicMaterial).opacity=0.6+Math.sin(tn*1.5)*0.2;
      // Bow wave amplitude — speed-responsive
      if(bowWaveGeo){const bp=bowWaveGeo.getAttribute('position');const sF=Math.min(1,hSpd/15);
        for(let i=0;i<bp.count;i++)bp.setY(i,0.02+Math.sin(tn*2+i*0.3)*0.015*sF);bp.needsUpdate=true;
        bwMat.opacity=0.03+sF*0.06;}
      // Wake drift — speed-responsive
      if(wkGeo){const wp=wkGeo.getAttribute('position');const dr=0.015+hSpd*0.002;
        for(let i=0;i<wp.count;i++){let z=wp.getZ(i)-dr;if(z<-7.5){z=-1.9-Math.random()*0.3;wp.setX(i,(Math.random()-0.5)*0.15);}wp.setZ(i,z);}wp.needsUpdate=true;}
      // Bow spray — speed-responsive
      {const sp2=spGeo.getAttribute('position');const sF2=Math.min(1,hSpd/15);
        for(let i=0;i<sp2.count;i++){let y=sp2.getY(i)+0.008*sF2;if(y>0.35){y=0;sp2.setX(i,(Math.random()-0.5)*0.3);sp2.setZ(i,1.7+Math.random()*0.5);}sp2.setY(i,y);}sp2.needsUpdate=true;spMat.opacity=0.1+sF2*0.2;}
      // Sea displacement — 4-component wave system
      if(seaGeo){const sp3=seaGeo.getAttribute('position');
        for(let i=0;i<sp3.count;i++){const x=sp3.getX(i),y=sp3.getY(i);sp3.setZ(i,Math.sin(x*0.35+tn*0.7)*0.09+Math.cos(y*0.28+tn*0.45)*0.06+Math.sin(x*0.7+y*0.5+tn*1.1)*0.035+Math.cos(x*0.15-tn*0.3)*0.04);}sp3.needsUpdate=true;}
      r.render(sc,cam);})();
    const ro=new ResizeObserver(e=>{const{width:w,height:h}=e[0].contentRect;if(!w||!h)return;cam.aspect=w/h;cam.updateProjectionMatrix();r.setSize(w,h);});ro.observe(hullEl.parentElement!);
    return()=>{run=false;ro.disconnect();r.dispose();threeR=undefined;};
  });
  $effect(()=>{if(!telemetry)return;hTP=telemetry.physics.pitch_deg*Math.PI/180;hTR=telemetry.physics.roll_deg*Math.PI/180;hTW=telemetry.physics.trim_fuel_penalty_pct>0;hSpd=telemetry.navigation.speed_knots;});

  /* ═══════ NAV & VOYAGE ═════════════════════════════════════════════ */
  function voyPct():number{return telemetry?Math.min(100,(telemetry.ais.current_waypoint_index/WPS.length)*100):0;}
  const navItems=[
    {icon:'⌘',label:'TAC',id:'tactical'},{icon:'🗺',label:'VOY',id:'voyage'},{icon:'⚙',label:'ENG',id:'engine'},
    {icon:'📊',label:'CII',id:'compliance'},{icon:'🔧',label:'SET',id:'settings'},
  ];

  /* ═══════ GHOST ROUTE STATE ══════════════════════════════════════════ */
  let ghostLine: L.Polyline | undefined;
  let ghostMarker: L.CircleMarker | undefined;

  function navClick(idx: number) {
    activeNav = idx;
    currentView = navItems[idx].id as typeof currentView;
    document.querySelector('.vp')?.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Keyboard shortcuts (F2-F4, F8, F9) matching React repo
  const fKeyMap: Record<string, number> = { F2: 0, F3: 1, F4: 2, F8: 3, F9: 4 };
  function handleKeydown(e: KeyboardEvent) {
    const idx = fKeyMap[e.key];
    if (idx !== undefined) { e.preventDefault(); navClick(idx); }
  }

  /* ═══════ LSTM ANOMALY DETECTION STATE ═══════════════════════════════ */
  let lstmMSE = $state(0);
  const lstmThreshold = 0.75;
  let lstmHistory = $state<number[]>([]);
  let engineFaultState = $state<{port:'healthy'|'warning'|'fault',starboard:'healthy'|'warning'|'fault'}>({port:'healthy',starboard:'healthy'});
  let predictiveDays = $state(0);
  $effect(() => {
    if (!telemetry) return;
    const rpmDev = Math.abs(telemetry.engine.rpm - 120) / 120;
    const tempDev = (telemetry.engine.temperature_c - 400) / 150;
    const mse = Math.max(0, 0.3 + rpmDev * 1.2 + tempDev * 0.8 + (Math.random() - 0.5) * 0.15);
    lstmMSE = mse;
    const prev = untrack(() => lstmHistory);
    const newHist = [...prev.slice(-(SPARK_LEN-1)), mse];
    lstmHistory = newHist;
    const trend = newHist.length > 10 ? (newHist.slice(-5).reduce((a,b)=>a+b,0)/5 - newHist.slice(-10,-5).reduce((a,b)=>a+b,0)/5) : 0;
    predictiveDays = trend > 0.01 ? Math.max(1, Math.round((1.5 - mse) / trend)) : 99;
    engineFaultState = {
      port: mse < 0.5 ? 'healthy' : mse < 0.75 ? 'warning' : 'fault',
      starboard: telemetry.engine.temperature_c > 480 ? 'fault' : telemetry.engine.temperature_c > 450 ? 'warning' : 'healthy'
    };
  });
</script>

<!-- ═══════ TEMPLATE ══════════════════════════════════════════════════════ -->
<svelte:window onkeydown={handleKeydown} />
{#if telemetry && derived}
<div class="scan-ol"></div>
<div class="shell">
  <!-- ── SIDE NAV ──────────────────────────────────────────────────────── -->
  <nav class="snav">
    <div class="nb"><svg class="icg-logo" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="gShield" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#FFD700"/><stop offset="100%" stop-color="#B8860B"/></linearGradient><linearGradient id="gAnchor" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#c0c0c0"/></linearGradient></defs><path d="M50 2 L92 25 L92 70 Q92 100 50 118 Q8 100 8 70 L8 25 Z" fill="none" stroke="url(#gShield)" stroke-width="3"/><path d="M50 8 L86 28 L86 68 Q86 95 50 112 Q14 95 14 68 L14 28 Z" fill="rgba(10,20,50,0.85)" stroke="none"/><circle cx="50" cy="18" r="6" fill="none" stroke="#FFD700" stroke-width="1.5"/><circle cx="50" cy="18" r="2" fill="#FFD700"/><line x1="50" y1="24" x2="50" y2="28" stroke="#FFD700" stroke-width="1.2"/><line x1="42" y1="28" x2="58" y2="28" stroke="#FFD700" stroke-width="1.2"/><g stroke="url(#gAnchor)" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="50" y1="34" x2="50" y2="85"/><path d="M37 44 L50 34 L63 44"/><line x1="40" y1="42" x2="60" y2="42"/><circle cx="50" cy="32" r="3" fill="none"/><path d="M32 78 Q32 60 50 58 Q68 60 68 78" fill="none"/><line x1="32" y1="78" x2="28" y2="82"/><line x1="68" y1="78" x2="72" y2="82"/></g><text x="50" y="98" text-anchor="middle" fill="#FFD700" font-size="5.5" font-weight="700" font-family="sans-serif" letter-spacing="0.8">INDIAN COAST GUARD</text><text x="50" y="107" text-anchor="middle" fill="#00ffcc" font-size="7" font-weight="800" font-family="monospace" letter-spacing="1.5">SAMUDRA</text></svg></div><div class="nd"></div>
    {#each navItems as ni, idx}<button class="ni" class:active={activeNav===idx} onclick={()=>navClick(idx)}><span class="ni-i">{ni.icon}</span><span class="ni-l">{ni.label}</span></button>{/each}
    <div class="ns"></div>
    <div class="nst"><div class="cd" class:online={connected}></div><span class="cl">{connected?'LIVE':'OFF'}</span><span class="cf">{fps}hz</span></div>
  </nav>

  <!-- ── VIEWPORT ──────────────────────────────────────────────────────── -->
  <div class="vp">
    <!-- DATA TICKER -->
    <div class="ticker"><div class="ticker-track">
      <span class="tk-seg tk-teal">◆ SOG {telemetry.navigation.speed_knots.toFixed(2)}kn</span>
      <span class="tk-seg tk-amber">◆ FUEL {telemetry.engine.fuel_flow_kgh.toFixed(0)}kg/h</span>
      <span class="tk-seg tk-cyan">◆ PWR {telemetry.engine.power_kw.toFixed(0)}kW</span>
      <span class="tk-seg tk-green">◆ RPM {telemetry.engine.rpm.toFixed(1)}</span>
      <span class="tk-seg tk-purple">◆ PPO {telemetry.drl_optimization.ppo_reward.toFixed(3)}</span>
      <span class="tk-seg tk-amber">◆ SFOC {telemetry.engine.sfoc_gkwh.toFixed(1)}g/kWh</span>
      <span class="tk-seg tk-red">◆ TEMP {telemetry.engine.temperature_c.toFixed(0)}°C</span>
      <span class="tk-seg tk-cyan">◆ HDG {telemetry.navigation.heading_deg.toFixed(1)}°</span>
      <span class="tk-seg tk-teal">◆ ETA-WP {derived.timeToWpH.toFixed(1)}h</span>
      <span class="tk-seg tk-green">◆ CII {telemetry.cii_segregation.cii_rating_corrected}</span>
      <span class="tk-seg tk-purple">◆ Fn {derived.fn.toFixed(4)}</span>
      <span class="tk-seg tk-amber">◆ SEA-MRG {derived.seaMrg.toFixed(1)}%</span>
      <span class="tk-seg tk-red">◆ CO₂ {derived.co2RateKgH.toFixed(0)}kg/h</span>
      <span class="tk-seg tk-cyan">◆ ENDURE {derived.endDays.toFixed(1)}d</span>
      <span class="tk-seg tk-teal">◆ RANGE {derived.rangeNM.toFixed(0)}nm</span>
      <span class="tk-seg tk-green">◆ ADM-C {telemetry.physics.admiralty_coefficient.toFixed(1)}</span>
      <span class="tk-seg tk-amber">◆ WIND {telemetry.environment.wind_speed_kts.toFixed(0)}kts</span>
      <span class="tk-seg tk-purple">◆ BIO {telemetry.ai_predictive_curve.penalty_pct.toFixed(1)}%</span>
      <!-- duplicate for seamless scroll -->
      <span class="tk-seg tk-teal">◆ SOG {telemetry.navigation.speed_knots.toFixed(2)}kn</span>
      <span class="tk-seg tk-amber">◆ FUEL {telemetry.engine.fuel_flow_kgh.toFixed(0)}kg/h</span>
      <span class="tk-seg tk-cyan">◆ PWR {telemetry.engine.power_kw.toFixed(0)}kW</span>
      <span class="tk-seg tk-green">◆ RPM {telemetry.engine.rpm.toFixed(1)}</span>
      <span class="tk-seg tk-purple">◆ PPO {telemetry.drl_optimization.ppo_reward.toFixed(3)}</span>
      <span class="tk-seg tk-amber">◆ SFOC {telemetry.engine.sfoc_gkwh.toFixed(1)}g/kWh</span>
    </div></div>

    <!-- KPI RIBBON -->
    <div class="kpi-r">
      <div class="kg"><span class="kt">SAMUDRA</span><span class="ks">TACTICAL COMMAND v4.0</span></div>
      <div class="k"><div class="kl">SOG<span class="ktr ktr-{sparkTrend(sparkSOG)}">{sparkTrend(sparkSOG)==='up'?'▲':sparkTrend(sparkSOG)==='down'?'▼':'—'}</span></div><div class="kv">{telemetry.navigation.speed_knots.toFixed(2)}<small>kn</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkSOG,44,10)} fill="none" stroke={OB.teal} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">RPM<span class="ktr ktr-{sparkTrend(sparkRPM)}">{sparkTrend(sparkRPM)==='up'?'▲':sparkTrend(sparkRPM)==='down'?'▼':'—'}</span></div><div class="kv">{telemetry.engine.rpm.toFixed(1)}</div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkRPM,44,10)} fill="none" stroke={OB.cyan} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">FUEL<span class="ktr ktr-{sparkTrend(sparkFuel)}">{sparkTrend(sparkFuel)==='up'?'▲':sparkTrend(sparkFuel)==='down'?'▼':'—'}</span></div><div class="kv">{telemetry.engine.fuel_flow_kgh.toFixed(0)}<small>kg/h</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkFuel,44,10)} fill="none" stroke={OB.amber} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">POWER<span class="ktr ktr-{sparkTrend(sparkPower)}">{sparkTrend(sparkPower)==='up'?'▲':sparkTrend(sparkPower)==='down'?'▼':'—'}</span></div><div class="kv">{telemetry.engine.power_kw.toFixed(0)}<small>kW</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkPower,44,10)} fill="none" stroke={OB.purple} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">SFOC<span class="ktr ktr-{sparkTrend(sparkSFOC)}">{sparkTrend(sparkSFOC)==='up'?'▲':sparkTrend(sparkSFOC)==='down'?'▼':'—'}</span></div><div class="kv">{telemetry.engine.sfoc_gkwh.toFixed(1)}<small>g/kWh</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkSFOC,44,10)} fill="none" stroke={OB.blue} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">η<span class="ktr ktr-{sparkTrend(sparkEta)}">{sparkTrend(sparkEta)==='up'?'▲':sparkTrend(sparkEta)==='down'?'▼':'—'}</span></div><div class="kv">{(telemetry.physics.thermal_efficiency*100).toFixed(1)}<small>%</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkEta,44,10)} fill="none" stroke={OB.green} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">TEMP<span class="ktr ktr-{sparkTrend(sparkTemp)}">{sparkTrend(sparkTemp)==='up'?'▲':sparkTrend(sparkTemp)==='down'?'▼':'—'}</span></div><div class="kv">{telemetry.engine.temperature_c.toFixed(0)}<small>°C</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkTemp,44,10)} fill="none" stroke={OB.red} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">MCR<span class="ktr ktr-{sparkTrend(sparkMCR)}">{sparkTrend(sparkMCR)==='up'?'▲':sparkTrend(sparkMCR)==='down'?'▼':'—'}</span></div><div class="kv">{telemetry.drl_optimization.mcr_load_pct.toFixed(1)}<small>%</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkMCR,44,10)} fill="none" stroke={OB.magenta} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">BIO<span class="ktr ktr-{sparkTrend(sparkBRC)}">{sparkTrend(sparkBRC)==='up'?'▲':sparkTrend(sparkBRC)==='down'?'▼':'—'}</span></div><div class="kv">{(telemetry.ai_predictive_curve.biological_roughness_coefficient*10000).toFixed(1)}<small>μ</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkBRC,44,10)} fill="none" stroke={OB.amber} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">CII<span class="ktr ktr-{sparkTrend(sparkCII)}">{sparkTrend(sparkCII)==='up'?'▲':sparkTrend(sparkCII)==='down'?'▼':'—'}</span></div><div class="kv" style="color:{ciiColor(telemetry.cii_segregation.cii_rating_corrected)}">{telemetry.cii_segregation.cii_rating_corrected}<small>{telemetry.cii_segregation.cii_attained_corrected.toFixed(3)}</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkCII,44,10)} fill="none" stroke={ciiColor(telemetry.cii_segregation.cii_rating_corrected)} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">Fn</div><div class="kv">{derived.fn.toFixed(4)}</div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkFrn,44,10)} fill="none" stroke={OB.blue} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">WAVE<span class="ktr ktr-{sparkTrend(sparkWave)}">{sparkTrend(sparkWave)==='up'?'▲':sparkTrend(sparkWave)==='down'?'▼':'—'}</span></div><div class="kv">{telemetry.environment.wave_height_m.toFixed(1)}<small>m</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkWave,44,10)} fill="none" stroke={OB.blue} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">CO₂<span class="ktr ktr-{sparkTrend(sparkCO2)}">{sparkTrend(sparkCO2)==='up'?'▲':sparkTrend(sparkCO2)==='down'?'▼':'—'}</span></div><div class="kv">{derived.co2RateKgH.toFixed(0)}<small>kg/h</small></div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkCO2,44,10)} fill="none" stroke={OB.red} stroke-width="1"/></svg></div>
      <div class="k"><div class="kl">ADM</div><div class="kv">{telemetry.physics.admiralty_coefficient.toFixed(1)}</div><svg class="ks-v" viewBox="0 0 44 10"><path d={sparkPath(sparkAdm,44,10)} fill="none" stroke={OB.teal} stroke-width="1"/></svg></div>
      <div class="kclk"><span class="kc-utc">{utcClock}</span><span class="kc-l">UTC</span><span class="kc-m">{missionElapsed}</span></div>
    </div>

    <!-- VOYAGE -->
    <div class="voy">
      <span class="voy-l">VOY</span>
      <div class="voy-tk">
        <div class="voy-f" style="width:{voyPct()}%"></div>
        {#each WPS as _,i}<div class="voy-wp" class:passed={telemetry.ais.current_waypoint_index>i} class:cur={telemetry.ais.current_waypoint_index===i} style="left:{((i+1)/(WPS.length+1))*100}%"></div>{/each}
      </div>
      <span class="voy-pct">{voyPct().toFixed(0)}%</span>
      <span class="voy-info">WP{telemetry.ais.current_waypoint_index} → {telemetry.ais.distance_to_waypoint_nm.toFixed(1)}nm</span>
      <span class="voy-eta">ETA {derived.timeToWpH.toFixed(1)}h | {derived.fuelToWpKg.toFixed(0)}kg</span>
    </div>

    <!-- ALERT BANNERS -->
    {#if telemetry.physics.monsoon_active}<div class="ab ab-crit"><span class="ab-i">⛈</span><span class="ab-t">MONSOON ACTIVE — +{telemetry.physics.monsoon_resistance_pct.toFixed(0)}% resistance | Sea State {telemetry.environment.sea_state}</span></div>{/if}
    {#if telemetry.drl_optimization.ghost_route_active}<div class="ab ab-ghost"><span class="ab-i">👻</span><span class="ab-t">GHOST ROUTE — Δv {telemetry.drl_optimization.speed_reduction_kts.toFixed(1)}kn | Target {telemetry.drl_optimization.recommended_speed_kts.toFixed(1)}kn | Save {telemetry.drl_optimization.fuel_saving_kgh.toFixed(0)}kg/h</span></div>{/if}
    {#if telemetry.physics.trim_fuel_penalty_pct > 0}<div class="ab ab-warn"><span class="ab-i">⚖</span><span class="ab-t">TRIM PENALTY +{telemetry.physics.trim_fuel_penalty_pct.toFixed(1)}% | Pitch {telemetry.physics.pitch_deg.toFixed(1)}°</span></div>{/if}
    {#if !aiEnabled}<div class="ab ab-off"><span class="ab-i">⛔</span><span class="ab-t">AI SYSTEMS OFFLINE — Running baseline sea trial mode</span></div>{/if}

    <!-- OVERRIDE -->
    <div class="ovr"><div class="ovr-h"><span class="ovr-i">⚡</span><span class="ovr-t">MASTER OVERRIDE</span><span class="ovr-sp"></span>
      <span class="ovr-sub">MMSI {telemetry.ais.mmsi} | COG {telemetry.ais.cog_deg.toFixed(1)}°</span>
      <button class="ovr-btn" class:on={aiEnabled} class:off={!aiEnabled} onclick={toggleAiMode}>
        <div class="tog-tk"><div class="tog-th"></div></div><span class="tog-s">{aiEnabled?'PINN/DRL ON':'BASELINE'}</span>
      </button>
    </div></div>

    <!-- ── PAGE TITLE BAR ───────────────────────────────────────────── -->
    <div class="page-title-bar">
      <span class="pt-icon">{navItems[activeNav]?.icon ?? '⌘'}</span>
      <h1 class="pt-name">{#if currentView === 'tactical'}TACTICAL CENTER{:else if currentView === 'voyage'}VOYAGE RE-OPTIMIZER{:else if currentView === 'engine'}ENGINE MONITORING HUB{:else if currentView === 'compliance'}CII & EEXI COMPLIANCE{:else}SYSTEM SETTINGS{/if}</h1>
      <span class="pt-fkey">{#if currentView === 'tactical'}F2{:else if currentView === 'voyage'}F3{:else if currentView === 'engine'}F4{:else if currentView === 'compliance'}F8{:else}F9{/if}</span>
      <span class="pt-sep"></span>
      <span class="pt-ai" class:pt-ai-on={aiEnabled} class:pt-ai-off={!aiEnabled}>{aiEnabled ? '● AI ACTIVE' : '○ BASELINE'}</span>
      <span class="pt-vessel">ENG V-442</span>
      <span class="pt-band">ISRO S-BAND</span>
      <button class="pt-bell" onclick={()=>notifCount=0}>🔔{#if notifCount>0}<span class="bell-dot">{notifCount}</span>{/if}</button>
    </div>

    <!-- ── MAIN CONTENT ─────────────────────────────────────────────── -->
    <div class="content">
      <div class="mc">
        <!-- GAUGE STRIP (12 gauges) -->
        <div class="gs" style:display={currentView === 'tactical' ? 'flex' : 'none'}>
          {#each [
            {l:'MCR',v:telemetry.drl_optimization.mcr_load_pct/100,d:telemetry.drl_optimization.mcr_load_pct.toFixed(1)+'%'},
            {l:'THERMAL',v:telemetry.physics.thermal_efficiency,d:(telemetry.physics.thermal_efficiency*100).toFixed(1)+'%'},
            {l:'CII',v:Math.min(1,telemetry.cii_segregation.cii_attained_corrected/telemetry.cii_segregation.cii_reference),d:telemetry.cii_segregation.cii_rating_corrected},
            {l:'BIO-F',v:telemetry.ai_predictive_curve.penalty_pct/15,d:telemetry.ai_predictive_curve.penalty_pct.toFixed(1)+'%'},
            {l:'SPD-R',v:telemetry.physics.speed_ratio,d:telemetry.physics.speed_ratio.toFixed(3)},
            {l:'WIND',v:telemetry.environment.wind_speed_kts/40,d:telemetry.environment.wind_speed_kts.toFixed(0)+'kts'},
            {l:'PPO-R',v:Math.max(0,telemetry.drl_optimization.ppo_reward+1)/2,d:telemetry.drl_optimization.ppo_reward.toFixed(3)},
            {l:'FUEL-E',v:derived.fuelEffPct/100,d:derived.fuelEffPct.toFixed(1)+'%'},
            {l:'PWR-M',v:(100-derived.powerMarginPct)/100,d:derived.powerMarginPct.toFixed(0)+'%'},
            {l:'SEA-ST',v:telemetry.environment.sea_state/9,d:'SS'+telemetry.environment.sea_state.toFixed(0)},
            {l:'FROUDE',v:derived.fn/.35,d:derived.fn.toFixed(4)},
            {l:'ENDURE',v:Math.min(1,derived.endDays/30),d:derived.endDays.toFixed(1)+'d'},
          ] as g}
          <div class="gc">
            <svg class="gsvg" viewBox="0 0 48 48"><path d={GTRACK} fill="none" stroke={OB.border} stroke-width="3" stroke-linecap="round"/><path d={gaugeArc(g.v,20,24,24)} fill="none" stroke={gColor(g.v)} stroke-width="3" stroke-linecap="round" filter="url(#glow)"/><text x="24" y="22" text-anchor="middle" fill={OB.textPri} font-size="8" font-family="'JetBrains Mono',monospace" font-weight="700">{g.d}</text><text x="24" y="42" text-anchor="middle" fill={OB.textDim} font-size="5.5" font-family="'JetBrains Mono',monospace" font-weight="600" letter-spacing=".04em">{g.l}</text>
              <defs><filter id="glow"><feGaussianBlur in="SourceGraphic" stdDeviation="1.5"/></filter></defs>
            </svg>
          </div>
          {/each}
          <div class="gc gc-tk"><div class="tk-v" style="color:{OB.green}">${derived.dailySavings.toFixed(0)}</div><div class="tk-u">SAVED/DAY</div><div class="tk-r">↓ {(telemetry.drl_optimization.fuel_saving_kgh).toFixed(0)} kg/h</div></div>
        </div>

        <!-- FUEL ACCOUNTING STRIP (expanded) -->
        <div class="fas" style:display={currentView === 'tactical' ? 'flex' : 'none'}>
          <div class="fi"><div class="fi-l">DAILY FUEL</div><div class="fi-v">{derived.dailyFuelT.toFixed(2)} <small>t/d</small></div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,derived.dailyFuelT/40*100)}%;background:{OB.amber}"></div></div></div>
          <div class="fi"><div class="fi-l">DAILY CO₂</div><div class="fi-v">{derived.dailyCO2T.toFixed(2)} <small>t/d</small></div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,derived.dailyCO2T/120*100)}%;background:{OB.red}"></div></div></div>
          <div class="fi"><div class="fi-l">DAILY COST</div><div class="fi-v">${derived.dailyFuelCost.toFixed(0)}</div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,derived.dailyFuelCost/20000*100)}%;background:{OB.amber}"></div></div></div>
          <div class="fi"><div class="fi-l">BIO WASTE</div><div class="fi-v">${derived.hullROI.toFixed(0)} <small>/d</small></div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,derived.hullROI/2000*100)}%;background:{OB.purple}"></div></div></div>
          <div class="fi"><div class="fi-l">EFF</div><div class="fi-v">{derived.fuelEffPct.toFixed(1)}%</div><div class="fi-b"><div class="fi-bf" style="width:{derived.fuelEffPct}%;background:{OB.green}"></div></div></div>
          <div class="fi"><div class="fi-l">PWR MARGIN</div><div class="fi-v">{derived.powerMarginPct.toFixed(0)}%</div><div class="fi-b"><div class="fi-bf" style="width:{Math.max(0,derived.powerMarginPct)}%;background:{OB.cyan}"></div></div></div>
          <div class="fi"><div class="fi-l">SFOC</div><div class="fi-v">{telemetry.engine.sfoc_gkwh.toFixed(1)} <small>g/kWh</small></div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,telemetry.engine.sfoc_gkwh/250*100)}%;background:{OB.blue}"></div></div></div>
          <div class="fi"><div class="fi-l">TOTAL FUEL</div><div class="fi-v">{(derived.totalFuelKg/1000).toFixed(2)} <small>t</small></div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,derived.totalFuelKg/(FUEL_CAPACITY_TONS*1000)*100)}%;background:{OB.amber}"></div></div></div>
          <div class="fi"><div class="fi-l">TOTAL CO₂</div><div class="fi-v">{(derived.totalCO2/1000).toFixed(2)} <small>t</small></div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,derived.totalCO2/100000*100)}%;background:{OB.red}"></div></div></div>
          <div class="fi"><div class="fi-l">FUEL REM</div><div class="fi-v">{(derived.fuelRemainKg/1000).toFixed(1)} <small>t</small></div><div class="fi-b"><div class="fi-bf" style="width:{derived.fuelRemainKg/(FUEL_CAPACITY_TONS*1000)*100}%;background:{OB.green}"></div></div></div>
          <div class="fi"><div class="fi-l">RANGE</div><div class="fi-v">{derived.rangeNM.toFixed(0)} <small>nm</small></div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,derived.rangeNM/5000*100)}%;background:{OB.teal}"></div></div></div>
          <div class="fi"><div class="fi-l">ENDURANCE</div><div class="fi-v">{derived.endDays.toFixed(1)} <small>d</small></div><div class="fi-b"><div class="fi-bf" style="width:{Math.min(100,derived.endDays/30*100)}%;background:{OB.cyan}"></div></div></div>
        </div>

        <!-- 2 CHARTS ROW -->
        <div class="r2" style:display={currentView === 'tactical' ? 'grid' : 'none'}>
          <div class="pnl cp"><div class="ph"><h2>PINN FUEL OPTIMIZATION CURVE</h2><span class="ptag pt-t">NEURAL</span><span class="ptag pt-w">Bio Δ{telemetry.ai_predictive_curve.penalty_pct.toFixed(1)}%</span></div><div class="cw"><canvas bind:this={c1El}></canvas></div></div>
          <div class="pnl cp"><div class="ph"><h2>REAL-TIME TELEMETRY STREAM</h2><span class="ptag">{totalFrames}f</span><span class="ptag pt-t">4Hz</span></div><div class="cw"><canvas bind:this={c2El}></canvas></div></div>
        </div>

        <!-- ══ HERO ROW: 3D HULL + TACTICAL MAP (PRIMARY USP) ═══════════ -->
        <div class="r2-hero" bind:this={sectionRefs['nav']} style:display={currentView === 'tactical' || currentView === 'voyage' ? 'grid' : 'none'}>
          <div class="pnl hero-pnl"><div class="ph hero-ph"><h2>⚓ 3D HULL DYNAMICS — DIGITAL TWIN</h2><span class="ptag pt-t">LIVE</span><span class="ptag">Δ2350t</span><span class="ptag">L91m×B14.2m</span>
            <span class="ptag" style="color:{engineFaultState.port==='healthy'?OB.green:engineFaultState.port==='warning'?OB.amber:OB.red}">PORT {engineFaultState.port.toUpperCase()}</span>
            <span class="ptag" style="color:{engineFaultState.starboard==='healthy'?OB.green:engineFaultState.starboard==='warning'?OB.amber:OB.red}">STBD {engineFaultState.starboard.toUpperCase()}</span>
          </div>
            <div class="hw-hero"><canvas bind:this={hullEl}></canvas>
              <div class="hull-overlay">
                <div class="hull-ol-row"><span class="hull-ol-label">PITCH</span><span class="hull-ol-val">{telemetry.physics.pitch_deg.toFixed(2)}°</span></div>
                <div class="hull-ol-row"><span class="hull-ol-label">ROLL</span><span class="hull-ol-val">{telemetry.physics.roll_deg.toFixed(2)}°</span></div>
                <div class="hull-ol-row"><span class="hull-ol-label">TRIM Δ</span><span class="hull-ol-val" style="color:{telemetry.physics.trim_fuel_penalty_pct>0?OB.amber:OB.green}">{telemetry.physics.trim_fuel_penalty_pct.toFixed(1)}%</span></div>
                <div class="hull-ol-row"><span class="hull-ol-label">DRAFT</span><span class="hull-ol-val">FWD 4.2m / AFT 5.1m</span></div>
                <div class="hull-ol-row"><span class="hull-ol-label">BIO-R</span><span class="hull-ol-val" style="color:{telemetry.ai_predictive_curve.penalty_pct>5?OB.amber:OB.teal}">{(telemetry.ai_predictive_curve.biological_roughness_coefficient*10000).toFixed(1)}μm</span></div>
                <div class="hull-ol-row"><span class="hull-ol-label">HULL AGE</span><span class="hull-ol-val">{telemetry.ai_predictive_curve.hull_age_hours.toFixed(0)}h</span></div>
              </div>
              <div class="hull-advisory">
                <div class="ha-title">TRIM ADVISORY</div>
                {#if telemetry.physics.trim_fuel_penalty_pct > 0}
                  <div class="ha-item ha-warn">⚠ Adjust ballast: FWD +0.3m AFT -0.2m → +{(telemetry.physics.trim_fuel_penalty_pct * 0.8).toFixed(1)}% recovery</div>
                {:else}
                  <div class="ha-item ha-ok">✓ Trim optimal — no corrective action needed</div>
                {/if}
              </div>
            </div>
            <div class="hst-hero">
              <span>PITCH {telemetry.physics.pitch_deg.toFixed(2)}°</span>
              <span>ROLL {telemetry.physics.roll_deg.toFixed(2)}°</span>
              <span>BEAM 14.2m</span>
              <span>T 3.7m</span>
              <span>η {telemetry.physics.speed_ratio.toFixed(3)}</span>
              <span>GM {(1.2 - Math.abs(telemetry.physics.roll_deg)*0.02).toFixed(2)}m</span>
              <span>WAVE {telemetry.environment.wave_height_m.toFixed(1)}m</span>
              <span style="color:{engineFaultState.port==='healthy'?OB.green:OB.amber}">E1-PORT {engineFaultState.port.toUpperCase()}</span>
              <span style="color:{engineFaultState.starboard==='healthy'?OB.green:OB.red}">E2-STBD {engineFaultState.starboard.toUpperCase()}</span>
            </div>
          </div>
          <div class="pnl hero-pnl" class:ghost-glow={telemetry.drl_optimization.ghost_route_active}><div class="ph hero-ph"><h2>🗺 AIS TACTICAL MAP — DRL ROUTE OPTIMIZER</h2><span class="ptag pt-t">WP{telemetry.ais.current_waypoint_index}/{WPS.length}</span>
            {#if telemetry.drl_optimization.ghost_route_active}<span class="ptag pt-gh">👻 GHOST ROUTE</span>{/if}
            <span class="ptag">{telemetry.navigation.speed_knots.toFixed(1)}kn</span>
            <span class="ptag pt-t">HDG {telemetry.navigation.heading_deg.toFixed(0)}°</span>
          </div>
            <div class="mw-hero" bind:this={mapEl}></div>
            <div class="map-overlay">
              <div class="map-ol-section">
                <div class="map-ol-title">ROUTE INTELLIGENCE</div>
                <div class="map-ol-row"><span class="map-ol-label">DTW</span><span class="map-ol-val">{telemetry.ais.distance_to_waypoint_nm.toFixed(1)} nm</span></div>
                <div class="map-ol-row"><span class="map-ol-label">ETA WP</span><span class="map-ol-val">{derived.timeToWpH.toFixed(2)} h</span></div>
                <div class="map-ol-row"><span class="map-ol-label">FUEL/WP</span><span class="map-ol-val">{derived.fuelToWpKg.toFixed(0)} kg</span></div>
                <div class="map-ol-row"><span class="map-ol-label">WIND</span><span class="map-ol-val">{telemetry.environment.wind_speed_kts.toFixed(0)}kts @ {telemetry.environment.wind_direction_deg.toFixed(0)}°</span></div>
                <div class="map-ol-row"><span class="map-ol-label">SEA ST</span><span class="map-ol-val">SS{telemetry.environment.sea_state.toFixed(0)} — {telemetry.environment.wave_height_m.toFixed(1)}m</span></div>
                {#if telemetry.drl_optimization.ghost_route_active}
                <div class="map-ol-row map-drl"><span class="map-ol-label">DRL SPD</span><span class="map-ol-val">{telemetry.drl_optimization.recommended_speed_kts.toFixed(1)} kn</span></div>
                <div class="map-ol-row map-drl"><span class="map-ol-label">FUEL SAVE</span><span class="map-ol-val ro-green">{telemetry.drl_optimization.fuel_saving_kgh.toFixed(0)} kg/h</span></div>
                <div class="map-ol-row map-drl"><span class="map-ol-label">ETA Δ</span><span class="map-ol-val">{(telemetry.drl_optimization.arrival_delta_s/60).toFixed(1)} min</span></div>
                <div class="map-ol-row map-drl" style="justify-content:center;padding-top:2px;pointer-events:auto;"><button class="ghost-accept-btn">ACCEPT GHOST ROUTE</button></div>
                {/if}
              </div>
            </div>
            <div class="nmea-hero">
              <span class="nmea-label">NMEA</span> {telemetry.ais.nmea_sentence}
              <span class="nmea-sep">|</span>
              <span class="nmea-label">MMSI</span> {telemetry.ais.mmsi}
              <span class="nmea-sep">|</span>
              <span class="nmea-label">COG</span> {telemetry.ais.cog_deg.toFixed(1)}°
              <span class="nmea-sep">|</span>
              <span class="nmea-label">LAT</span> {telemetry.navigation.latitude.toFixed(4)}°N
              <span class="nmea-sep">|</span>
              <span class="nmea-label">LON</span> {telemetry.navigation.longitude.toFixed(4)}°E
            </div>
          </div>
        </div>

        <!-- CHART ROW: SPEED-POWER + EFFICIENCY -->
        <div class="r2" style:display={currentView === 'tactical' ? 'grid' : 'none'}>
          <div class="pnl cp"><div class="ph"><h2>SPEED—POWER V³ LAW</h2><span class="ptag">P∝V³</span></div><div class="cw"><canvas bind:this={c3El}></canvas></div></div>
          <div class="pnl cp"><div class="ph"><h2>EFFICIENCY TREND</h2><span class="ptag pt-t">η+EFF</span></div><div class="cw"><canvas bind:this={c4El}></canvas></div></div>
        </div>

        <!-- QUAD ROW: CII + DRL + RISK + FUEL ECON -->
        <div class="r4" style:display={currentView === 'voyage' || currentView === 'compliance' ? 'grid' : 'none'}>
          <!-- CII -->
          <div class="pnl" bind:this={sectionRefs['cii']}><div class="ph"><h2>CII TACTICAL COMPLIANCE</h2>
            <span class="ptag" class:badge-transit={telemetry.cii_segregation.mission_state==='transit'} class:badge-loiter={telemetry.cii_segregation.mission_state==='tactical_loiter'}>{telemetry.cii_segregation.mission_state.toUpperCase()}</span></div>
            <div class="cii-b">
              <div class="cii-rtg">
                <div class="cii-bx"><div class="cii-bl">RAW</div><div class="cii-lt" style="color:{ciiColor(telemetry.cii_segregation.cii_rating_raw)}">{telemetry.cii_segregation.cii_rating_raw}</div><div class="cii-nm">{telemetry.cii_segregation.cii_attained_raw.toFixed(4)}</div></div>
                <div class="cii-sp"></div>
                <div class="cii-bx"><div class="cii-bl">CORR</div><div class="cii-lt" style="color:{ciiColor(telemetry.cii_segregation.cii_rating_corrected)}">{telemetry.cii_segregation.cii_rating_corrected}</div><div class="cii-nm">{telemetry.cii_segregation.cii_attained_corrected.toFixed(4)}</div></div>
              </div>
              <div class="cii-sc"><div class="cii-sb">{#each ['A','B','C','D','E'] as r}<div class="cii-sg" style="background:{ciiColor(r)}">{r}</div>{/each}</div></div>
              <div class="cii-ref">REF: {telemetry.cii_segregation.cii_reference.toFixed(4)}</div>
              <div class="cii-grid">
                <div class="cr"><span class="crl">Transit CO₂</span><span class="crv tc">{telemetry.cii_segregation.transit_co2_tonnes.toFixed(3)}t</span></div>
                <div class="cr"><span class="crl">Loiter CO₂</span><span class="crv lc">{telemetry.cii_segregation.loiter_co2_tonnes.toFixed(3)}t</span></div>
                <div class="cr"><span class="crl">Transit Fuel</span><span class="crv tc">{telemetry.cii_segregation.transit_fuel_tonnes.toFixed(3)}t</span></div>
                <div class="cr"><span class="crl">Loiter Fuel</span><span class="crv lc">{telemetry.cii_segregation.loiter_fuel_tonnes.toFixed(3)}t</span></div>
                <div class="cr"><span class="crl">Transit Dist</span><span class="crv">{telemetry.cii_segregation.transit_distance_nm.toFixed(1)}nm</span></div>
                <div class="cr"><span class="crl">Elapsed</span><span class="crv">{telemetry.cii_segregation.elapsed_hours.toFixed(2)}h</span></div>
                <div class="cr"><span class="crl">Transit #</span><span class="crv">{telemetry.cii_segregation.transit_events}</span></div>
                <div class="cr"><span class="crl">Loiter #</span><span class="crv">{telemetry.cii_segregation.loiter_events}</span></div>
              </div>
            </div>
          </div>

          <!-- DBSCAN EMISSION SEGREGATION (from repo) -->
          <div class="pnl" style:display={currentView === 'compliance' ? 'block' : 'none'}>
            <div class="ph"><h2>DBSCAN EMISSION SEGREGATION</h2><span class="ptag pt-t">AI CLUSTERED</span></div>
            <div style="padding:4px 6px">
              <div class="dbscan-kpis">
                <div class="dbscan-kpi"><span class="dbscan-kl">Total Fuel</span><span class="dbscan-kv">1,245.8 MT</span><span class="dbscan-kd" style="color:{OB.amber}">+2.4%</span></div>
                <div class="dbscan-kpi"><span class="dbscan-kl">DBSCAN Exempt</span><span class="dbscan-kv">412.3 MT</span></div>
                <div class="dbscan-kpi"><span class="dbscan-kl">AER (CII)</span><span class="dbscan-kv">{telemetry.cii_segregation.cii_attained_corrected.toFixed(2)}</span></div>
              </div>
              <div style="height:140px"><canvas bind:this={c7El}></canvas></div>
            </div>
          </div>

          <!-- SEGMENT CLASSIFICATION TABLE (from repo) -->
          <div class="pnl" style:display={currentView === 'compliance' ? 'block' : 'none'}>
            <div class="ph"><h2>SEGMENT CLASSIFICATION</h2>
              <span class="ptag">AUTOMATED MARPOL VI</span>
              <button class="imo-btn" onclick={()=>pushAlert('IMO DCS Report generated — ready for download','INFO')}>📥 IMO DCS REPORT</button>
            </div>
            <div class="seg-table-w">
              <table class="seg-table">
                <thead><tr><th>TIMEFRAME</th><th>MODE (AI)</th><th>FUEL (MT)</th></tr></thead>
                <tbody>
                  {#each segmentData as seg}
                  <tr>
                    <td>{seg.timeframe}</td>
                    <td><span class="seg-mode" class:seg-transit={seg.type==='transit'} class:seg-loiter={seg.type==='loiter'} class:seg-anchor={seg.type==='anchor'}>{seg.mode}</span></td>
                    <td style="color:{seg.fuel>20?OB.amber:OB.textSec}">{seg.fuel.toFixed(1)}</td>
                  </tr>
                  {/each}
                </tbody>
              </table>
              <div class="seg-footer">
                <span style="color:{OB.textDim}">DB Sync: <span style="color:{OB.green}">● ACTIVE</span></span>
              </div>
            </div>
          </div>

          <!-- DRL -->
          <div class="pnl" class:ghost-glow={telemetry.drl_optimization.ghost_route_active} bind:this={sectionRefs['ai']}>
            <div class="ph"><h2>DRL PPO OPTIMIZER</h2>{#if telemetry.drl_optimization.ghost_route_active}<span class="ptag pt-gh">GHOST</span>{/if}<span class="ptag">ε{telemetry.drl_optimization.ppo_reward.toFixed(3)}</span></div>
            <div class="drl-b">
              <div class="drl-sp"><div class="drl-bx"><div class="drl-lb">CURRENT</div><div class="drl-bg">{telemetry.drl_optimization.current_speed_kts.toFixed(1)}</div><div class="drl-u">kn</div></div>
                <span class="drl-ar">→</span>
                <div class="drl-bx drl-rec"><div class="drl-lb">RECOMMEND</div><div class="drl-bg">{telemetry.drl_optimization.recommended_speed_kts.toFixed(1)}</div><div class="drl-u">kn</div></div>
                <div class="drl-dt">Δ{telemetry.drl_optimization.speed_reduction_kts.toFixed(1)}kn</div>
              </div>
              <div class="rdts">
                <div class="ro"><span class="ro-l">Fuel Save</span><span class="ro-v ro-green">{telemetry.drl_optimization.fuel_saving_kgh.toFixed(1)} kg/h</span></div>
                <div class="ro"><span class="ro-l">Total Saved</span><span class="ro-v ro-green">{telemetry.drl_optimization.total_fuel_saved_kg.toFixed(0)} kg</span></div>
                <div class="ro"><span class="ro-l">MCR</span><span class="ro-v" class:ro-band={telemetry.drl_optimization.in_mcr_band}>{telemetry.drl_optimization.mcr_load_pct.toFixed(1)}%</span></div>
                <div class="ro"><span class="ro-l">Rec MCR</span><span class="ro-v ro-purple">{telemetry.drl_optimization.recommended_mcr_load_pct.toFixed(1)}%</span></div>
                <div class="ro"><span class="ro-l">ETA Δ</span><span class="ro-v">{telemetry.drl_optimization.arrival_delta_s.toFixed(0)}s</span></div>
                <div class="ro"><span class="ro-l">PPO Reward</span><span class="ro-v ro-purple">{telemetry.drl_optimization.ppo_reward.toFixed(4)}</span></div>
                <div class="ro"><span class="ro-l">Load Bal</span><span class="ro-v">{derived.loadBalance.toFixed(0)}%</span></div>
              </div>
              <div class="drl-trace"><div class="trace-l">REWARD TRACE</div><svg class="trace-svg" viewBox="0 0 200 24"><path d={sparkArea(sparkReward,200,24)} fill={OB.purple+'15'}/><path d={sparkPath(sparkReward,200,24)} fill="none" stroke={OB.purple} stroke-width="1"/></svg></div>
            </div>
          </div>

          <!-- RISK -->
          <div class="pnl" bind:this={sectionRefs['risk']}>
            <div class="ph"><h2>RISK ASSESSMENT</h2><span class="ptag" style="color:{riskColor(derived.risk.overall)}">{riskLabel(derived.risk.overall)}</span></div>
            <div class="risk-b">
              <div class="risk-ov"><span class="risk-sc" style="color:{riskColor(derived.risk.overall)}">{derived.risk.overall}</span><span class="risk-of">/100</span></div>
              {#each [['ENGINE',derived.risk.eng],['NAV',derived.risk.nav],['ENVIRON',derived.risk.env],['COMPLIANCE',derived.risk.comp],['HULL',derived.risk.hull],['STRUCTUR',derived.risk.structural]] as [label,val]}
              <div class="rr"><span class="rr-l">{label}</span><div class="rr-b"><div class="rr-bf" style="width:{val}%;background:{riskColor(val as number)}"></div></div><span class="rr-v">{(val as number).toFixed(0)}</span></div>
              {/each}
            </div>
          </div>

          <!-- FUEL ECONOMICS -->
          <div class="pnl" bind:this={sectionRefs['fuel']}>
            <div class="ph"><h2>FUEL ECONOMICS</h2><span class="ptag pt-t">${derived.dailyFuelCost.toFixed(0)}/d</span></div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">Daily Fuel</span><span class="ro-v">{derived.dailyFuelT.toFixed(2)} t</span></div>
              <div class="ro"><span class="ro-l">Daily CO₂</span><span class="ro-v">{derived.dailyCO2T.toFixed(2)} t</span></div>
              <div class="ro"><span class="ro-l">Daily Cost</span><span class="ro-v ro-amber">${derived.dailyFuelCost.toFixed(0)}</span></div>
              <div class="ro"><span class="ro-l">AI Savings</span><span class="ro-v ro-green">${derived.dailySavings.toFixed(0)}/d</span></div>
              <div class="ro"><span class="ro-l">Hull Clean ROI</span><span class="ro-v ro-green">${derived.hullROI.toFixed(0)}/d</span></div>
              <div class="ro"><span class="ro-l">Fuel/WP</span><span class="ro-v">{derived.fuelToWpKg.toFixed(0)} kg</span></div>
              <div class="ro"><span class="ro-l">Fuel Remain</span><span class="ro-v">{(derived.fuelRemainKg/1000).toFixed(1)} t</span></div>
              <div class="ro"><span class="ro-l">Range</span><span class="ro-v ro-cyan">{derived.rangeNM.toFixed(0)} nm</span></div>
              <div class="ro"><span class="ro-l">Endurance</span><span class="ro-v ro-cyan">{derived.endDays.toFixed(1)} days</span></div>
              <div class="ro"><span class="ro-l">Spec Power</span><span class="ro-v">{derived.specPowerKwPerKn.toFixed(0)} kW/kn</span></div>
            </div>
          </div>
        </div>

        <!-- QUAD ROW: PROPULSION + EMISSIONS + ENVIRONMENT CHART + PERF BENCH -->
        <div class="r4" style:display={currentView === 'engine' || currentView === 'compliance' ? 'grid' : 'none'}>
          <!-- PROPULSION -->
          <div class="pnl" bind:this={sectionRefs['engine']}>
            <div class="ph"><h2>PROPULSION ANALYSIS</h2><span class="ptag pt-t">P∝V³</span></div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">Admiralty C</span><span class="ro-v">{telemetry.physics.admiralty_coefficient.toFixed(2)}</span></div>
              <div class="ro"><span class="ro-l">C Deviation</span><span class="ro-v" class:ro-amber={Math.abs(derived.propCoeffDev)>3}>{derived.propCoeffDev.toFixed(1)}%</span></div>
              <div class="ro"><span class="ro-l">Cubic Law P</span><span class="ro-v">{derived.cubicCalm.toFixed(0)} kW</span></div>
              <div class="ro"><span class="ro-l">Sea Margin</span><span class="ro-v">{derived.seaMrg.toFixed(1)}%</span></div>
              <div class="ro"><span class="ro-l">Speed Deficit</span><span class="ro-v">{derived.speedDef.toFixed(2)} kn</span></div>
              <div class="ro"><span class="ro-l">Froude №</span><span class="ro-v">{derived.fn.toFixed(4)}</span></div>
              <div class="ro"><span class="ro-l">Hull Eff Idx</span><span class="ro-v">{derived.hullEffIdx.toFixed(1)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{derived.hullEffIdx}%;background:{OB.teal}"></div></div></div>
              <div class="ro"><span class="ro-l">RPM Dev</span><span class="ro-v">{derived.rpmDevPct.toFixed(1)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{Math.min(100,derived.rpmDevPct*5)}%;background:{derived.rpmDevPct>5?OB.red:OB.green}"></div></div></div>
              <div class="ro"><span class="ro-l">Thermal Bdgt</span><span class="ro-v" style="color:{derived.thermalBudgetPct>85?OB.red:OB.textSec}">{derived.thermalBudgetPct.toFixed(0)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{derived.thermalBudgetPct}%;background:{heatColor(derived.thermalBudgetPct/100)}"></div></div></div>
            </div>
          </div>

          <!-- EMISSIONS -->
          <div class="pnl">
            <div class="ph"><h2>EMISSIONS TRACKER</h2><span class="ptag pt-w">IMO TIER III</span></div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">CO₂ Rate</span><span class="ro-v ro-red">{derived.co2RateKgH.toFixed(0)} kg/h</span></div>
              <div class="ro"><span class="ro-l">SOx Rate</span><span class="ro-v ro-amber">{derived.soxKgH.toFixed(1)} kg/h</span></div>
              <div class="ro"><span class="ro-l">NOx Rate</span><span class="ro-v ro-amber">{derived.noxKgH.toFixed(1)} kg/h</span></div>
              <div class="ro"><span class="ro-l">PM Rate</span><span class="ro-v">{derived.pmKgH.toFixed(2)} kg/h</span></div>
              <div class="ro"><span class="ro-l">Daily CO₂</span><span class="ro-v ro-red">{derived.dailyCO2T.toFixed(2)} t</span></div>
              <div class="ro"><span class="ro-l">Daily SOx</span><span class="ro-v">{(derived.soxKgH*24/1000).toFixed(3)} t</span></div>
              <div class="ro"><span class="ro-l">Daily NOx</span><span class="ro-v">{(derived.noxKgH*24/1000).toFixed(3)} t</span></div>
              <div class="ro"><span class="ro-l">Total CO₂</span><span class="ro-v">{(derived.totalCO2/1000).toFixed(2)} t</span></div>
              <div class="ro"><span class="ro-l">Carbon Factor</span><span class="ro-v">{CARBON_FACTOR}</span></div>
              <div class="ro"><span class="ro-l">ECA Zone</span><span class="ro-v ro-green">OUTSIDE</span></div>
            </div>
          </div>

          <!-- ENVIRONMENTAL CHART -->
          <div class="pnl cp"><div class="ph"><h2>ENVIRONMENTAL DATA</h2><span class="ptag">BFT {derived.bft}</span></div><div class="cw"><canvas bind:this={c5El}></canvas></div></div>

          <!-- PERFORMANCE BENCHMARK -->
          <div class="pnl" bind:this={sectionRefs['perf']}>
            <div class="ph"><h2>PERFORMANCE BENCHMARK</h2><span class="ptag pt-t">vs DESIGN</span></div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">Speed/Design</span><span class="ro-v">{(telemetry.navigation.speed_knots/DESIGN_SPEED_KTS*100).toFixed(1)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{telemetry.navigation.speed_knots/DESIGN_SPEED_KTS*100}%;background:{OB.teal}"></div></div></div>
              <div class="ro"><span class="ro-l">Power/Design</span><span class="ro-v">{(telemetry.engine.power_kw/DESIGN_POWER_KW*100).toFixed(1)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{telemetry.engine.power_kw/DESIGN_POWER_KW*100}%;background:{OB.cyan}"></div></div></div>
              <div class="ro"><span class="ro-l">SFOC/Target</span><span class="ro-v">{(telemetry.engine.sfoc_gkwh/185*100).toFixed(0)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{Math.min(100,telemetry.engine.sfoc_gkwh/185*100)}%;background:{telemetry.engine.sfoc_gkwh>200?OB.red:OB.green}"></div></div></div>
              <div class="ro"><span class="ro-l">Spec Power</span><span class="ro-v">{derived.specPowerKwPerKn.toFixed(0)} kW/kn</span></div>
              <div class="ro"><span class="ro-l">Sea Margin</span><span class="ro-v" style="color:{derived.seaMrg>15?OB.amber:OB.green}">{derived.seaMrg.toFixed(1)}%</span></div>
              <div class="ro"><span class="ro-l">Hull Eff</span><span class="ro-v">{derived.hullEffIdx.toFixed(0)}%</span></div>
              <div class="ro"><span class="ro-l">Monsoon Res</span><span class="ro-v" class:ro-red={telemetry.physics.monsoon_active}>{telemetry.physics.monsoon_resistance_pct.toFixed(1)}%</span></div>
              <div class="ro"><span class="ro-l">Trim Penalty</span><span class="ro-v">{telemetry.physics.trim_fuel_penalty_pct.toFixed(1)}%</span></div>
              <div class="ro"><span class="ro-l">Prop Coeff Δ</span><span class="ro-v">{derived.propCoeffDev.toFixed(1)}%</span></div>
            </div>
          </div>
        </div>

        <!-- DATA CARDS GRID -->
        <div class="cg" style:display={currentView === 'engine' || currentView === 'voyage' ? 'grid' : 'none'}>
          <!-- ENGINE -->
          <div class="pnl cd"><h3>⚙ ENGINE <small>MAN B&W</small></h3><div class="rdts">
            <div class="ro"><span class="ro-l">RPM</span><span class="ro-v">{telemetry.engine.rpm.toFixed(1)}</span><svg class="ms" viewBox="0 0 40 10"><path d={sparkPath(sparkRPM,40,10)} fill="none" stroke={OB.cyan} stroke-width=".8"/></svg></div>
            <div class="ro"><span class="ro-l">Power</span><span class="ro-v">{telemetry.engine.power_kw.toFixed(0)} kW</span><svg class="ms" viewBox="0 0 40 10"><path d={sparkPath(sparkPower,40,10)} fill="none" stroke={OB.purple} stroke-width=".8"/></svg></div>
            <div class="ro"><span class="ro-l">Fuel Flow</span><span class="ro-v">{telemetry.engine.fuel_flow_kgh.toFixed(0)} kg/h</span></div>
            <div class="ro"><span class="ro-l">Temp</span><span class="ro-v" style="color:{telemetry.engine.temperature_c>480?OB.red:OB.textSec}">{telemetry.engine.temperature_c.toFixed(0)}°C</span><div class="ro-bar"><div class="ro-bf" style="width:{telemetry.engine.temperature_c/550*100}%;background:{heatColor(telemetry.engine.temperature_c/550)}"></div></div></div>
            <div class="ro"><span class="ro-l">SFOC</span><span class="ro-v">{telemetry.engine.sfoc_gkwh.toFixed(1)} g/kWh</span></div>
            <div class="ro"><span class="ro-l">MCR Load</span><span class="ro-v">{telemetry.drl_optimization.mcr_load_pct.toFixed(1)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{telemetry.drl_optimization.mcr_load_pct}%;background:{gColor(telemetry.drl_optimization.mcr_load_pct/100)}"></div></div></div>
          </div></div>
          <!-- NAVIGATION -->
          <div class="pnl cd"><h3>🧭 NAVIGATION</h3><div class="rdts">
            <div class="ro"><span class="ro-l">SOG</span><span class="ro-v">{telemetry.navigation.speed_knots.toFixed(2)} kn</span></div>
            <div class="ro"><span class="ro-l">HDG</span><span class="ro-v">{telemetry.navigation.heading_deg.toFixed(1)}°</span></div>
            <div class="ro"><span class="ro-l">LAT</span><span class="ro-v">{telemetry.navigation.latitude.toFixed(4)}°N</span></div>
            <div class="ro"><span class="ro-l">LON</span><span class="ro-v">{telemetry.navigation.longitude.toFixed(4)}°E</span></div>
            <div class="ro"><span class="ro-l">COG</span><span class="ro-v">{telemetry.ais.cog_deg.toFixed(1)}°</span></div>
            <div class="ro"><span class="ro-l">DTW</span><span class="ro-v">{telemetry.ais.distance_to_waypoint_nm.toFixed(1)} nm</span></div>
          </div></div>
          <!-- ENVIRONMENT -->
          <div class="pnl cd" bind:this={sectionRefs['env']}><h3>🌊 ENVIRONMENT</h3><div class="rdts">
            <div class="ro"><span class="ro-l">Wind</span><span class="ro-v">{telemetry.environment.wind_speed_kts.toFixed(0)} kts / BFT{derived.bft}</span></div>
            <div class="ro"><span class="ro-l">Wind Dir</span><span class="ro-v">{telemetry.environment.wind_direction_deg.toFixed(0)}° (Rel {derived.relWindDeg.toFixed(0)}°)</span></div>
            <div class="ro"><span class="ro-l">Sea State</span><span class="ro-v">SS{telemetry.environment.sea_state.toFixed(0)}</span><div class="ro-bar"><div class="ro-bf" style="width:{telemetry.environment.sea_state/9*100}%;background:{telemetry.environment.sea_state>=5?OB.red:OB.cyan}"></div></div></div>
            <div class="ro"><span class="ro-l">Wave</span><span class="ro-v">{telemetry.environment.wave_height_m.toFixed(2)} m</span><svg class="ms" viewBox="0 0 40 10"><path d={sparkPath(sparkWave,40,10)} fill="none" stroke={OB.blue} stroke-width=".8"/></svg></div>
            <div class="ro"><span class="ro-l">SST</span><span class="ro-v">{telemetry.ai_predictive_curve.sea_surface_temp_c.toFixed(1)}°C</span></div>
            <div class="ro"><span class="ro-l">Monsoon</span><span class="ro-v" style="color:{telemetry.physics.monsoon_active?OB.red:OB.green}">{telemetry.physics.monsoon_active?'ACTIVE':'CLEAR'}</span></div>
          </div></div>
          <!-- HYDRODYNAMICS -->
          <div class="pnl cd"><h3>💧 HYDRODYNAMICS</h3><div class="rdts">
            <div class="ro"><span class="ro-l">Adm Coeff</span><span class="ro-v">{telemetry.physics.admiralty_coefficient.toFixed(2)}</span></div>
            <div class="ro"><span class="ro-l">Thermal η</span><span class="ro-v">{(telemetry.physics.thermal_efficiency*100).toFixed(1)}%</span></div>
            <div class="ro"><span class="ro-l">Speed Ratio</span><span class="ro-v">{telemetry.physics.speed_ratio.toFixed(3)}</span></div>
            <div class="ro"><span class="ro-l">Cubic Law P</span><span class="ro-v">{telemetry.physics.cubic_law_power_kw.toFixed(0)} kW</span></div>
            <div class="ro"><span class="ro-l">Monsoon +</span><span class="ro-v">{telemetry.physics.monsoon_resistance_pct.toFixed(1)}%</span></div>
            <div class="ro"><span class="ro-l">Trim Penalty</span><span class="ro-v">{telemetry.physics.trim_fuel_penalty_pct.toFixed(1)}%</span></div>
          </div></div>
          <!-- BIOFOULING -->
          <div class="pnl cd"><h3>🦠 BIOFOULING <small>PINN</small></h3><div class="rdts">
            <div class="ro"><span class="ro-l">BRC</span><span class="ro-v">{(telemetry.ai_predictive_curve.biological_roughness_coefficient*10000).toFixed(2)} μ</span><svg class="ms" viewBox="0 0 40 10"><path d={sparkPath(sparkBRC,40,10)} fill="none" stroke={OB.amber} stroke-width=".8"/></svg></div>
            <div class="ro"><span class="ro-l">Penalty</span><span class="ro-v" class:ro-amber={telemetry.ai_predictive_curve.penalty_pct>5}>{telemetry.ai_predictive_curve.penalty_pct.toFixed(1)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{Math.min(100,telemetry.ai_predictive_curve.penalty_pct*6.67)}%;background:{telemetry.ai_predictive_curve.penalty_pct>8?OB.red:OB.amber}"></div></div></div>
            <div class="ro"><span class="ro-l">Optimal Fuel</span><span class="ro-v ro-green">{telemetry.ai_predictive_curve.optimal_fuel_kgh.toFixed(0)} kg/h</span></div>
            <div class="ro"><span class="ro-l">Actual Fuel</span><span class="ro-v ro-amber">{telemetry.ai_predictive_curve.actual_fuel_kgh.toFixed(0)} kg/h</span></div>
            <div class="ro"><span class="ro-l">Hull Age</span><span class="ro-v">{telemetry.ai_predictive_curve.hull_age_hours.toFixed(0)} h</span></div>
            <div class="ro"><span class="ro-l">SST</span><span class="ro-v">{telemetry.ai_predictive_curve.sea_surface_temp_c.toFixed(1)}°C</span></div>
          </div></div>
          <!-- DRL DETAIL -->
          <div class="pnl cd" class:ghost-glow={telemetry.drl_optimization.ghost_route_active}><h3>🤖 DRL DETAIL <small>PPO</small></h3><div class="rdts">
            <div class="ro"><span class="ro-l">Ghost Route</span><span class="ro-v" style="color:{telemetry.drl_optimization.ghost_route_active?OB.purple:OB.textDim}">{telemetry.drl_optimization.ghost_route_active?'ENGAGED':'STANDBY'}</span></div>
            <div class="ro"><span class="ro-l">Rec Speed</span><span class="ro-v ro-purple">{telemetry.drl_optimization.recommended_speed_kts.toFixed(1)} kn</span></div>
            <div class="ro"><span class="ro-l">Δ Speed</span><span class="ro-v">{telemetry.drl_optimization.speed_reduction_kts.toFixed(2)} kn</span></div>
            <div class="ro"><span class="ro-l">ETA Planned</span><span class="ro-v">{telemetry.drl_optimization.eta_planned_s.toFixed(0)}s</span></div>
            <div class="ro"><span class="ro-l">ETA Current</span><span class="ro-v">{telemetry.drl_optimization.eta_current_s.toFixed(0)}s</span></div>
            <div class="ro"><span class="ro-l">PPO ε</span><span class="ro-v ro-purple">{telemetry.drl_optimization.ppo_reward.toFixed(4)}</span><svg class="ms" viewBox="0 0 40 10"><path d={sparkPath(sparkReward,40,10)} fill="none" stroke={OB.purple} stroke-width=".8"/></svg></div>
          </div></div>
          <!-- VOYAGE -->
          <div class="pnl cd"><h3>🗺 VOYAGE ANALYTICS</h3><div class="rdts">
            <div class="ro"><span class="ro-l">Waypoint</span><span class="ro-v">{telemetry.ais.current_waypoint_index}/{WPS.length}</span></div>
            <div class="ro"><span class="ro-l">DTW</span><span class="ro-v">{telemetry.ais.distance_to_waypoint_nm.toFixed(1)} nm</span></div>
            <div class="ro"><span class="ro-l">ETA WP</span><span class="ro-v">{derived.timeToWpH.toFixed(2)} h</span></div>
            <div class="ro"><span class="ro-l">Fuel/WP</span><span class="ro-v">{derived.fuelToWpKg.toFixed(0)} kg</span></div>
            <div class="ro"><span class="ro-l">Progress</span><span class="ro-v ro-teal">{voyPct().toFixed(1)}%</span></div>
            <div class="ro"><span class="ro-l">MMSI</span><span class="ro-v">{telemetry.ais.mmsi}</span></div>
          </div></div>
          <!-- MACHINERY HEALTH -->
          <div class="pnl cd"><h3>🔧 MACHINERY HEALTH</h3><div class="rdts">
            {#each [
              {l:'Main Engine',v:Math.min(100,100-derived.rpmDevPct*3)},{l:'Turbocharger',v:Math.min(100,derived.thermalBudgetPct>90?60:95)},
              {l:'Fuel System',v:Math.min(100,derived.fuelEffPct)},{l:'Cooling',v:Math.min(100,100-((telemetry.engine.temperature_c-300)/250)*60)},
              {l:'Exhaust',v:Math.min(100,100-((telemetry.engine.temperature_c-350)/200)*30)},{l:'Shaft/Prop',v:Math.min(100,derived.hullEffIdx)},
            ] as item}
            <div class="ro"><span class="ro-l">{item.l}</span><span class="ro-v" style="color:{item.v>80?OB.green:item.v>50?OB.amber:OB.red}">{item.v.toFixed(0)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{item.v}%;background:{heatColor(1-item.v/100)}"></div></div></div>
            {/each}
          </div></div>
        </div>

        <!-- LSTM ANOMALY + TWIN ENGINE + EDGE SYSTEMS (from SAMUDRA repo integration) -->
        <div class="lstm-strip" style:display={currentView === 'engine' || currentView === 'settings' ? 'grid' : 'none'}>
          <div class="pnl">
            <div class="ph"><h2>LSTM ANOMALY DETECTOR</h2>
              <span class="ptag" style="color:{lstmMSE>lstmThreshold?OB.red:lstmMSE>0.5?OB.amber:OB.green}">{lstmMSE>lstmThreshold?'ANOMALY':'NOMINAL'}</span>
              <span class="ptag">MSE {lstmMSE.toFixed(3)}</span>
            </div>
            <div class="rdts" style="padding:4px 6px">
              <div class="lstm-mse" style="color:{lstmMSE>lstmThreshold?OB.red:lstmMSE>0.5?OB.amber:OB.green};text-align:center">{lstmMSE.toFixed(4)}</div>
              <div class="lstm-thr" style="text-align:center">THR: {lstmThreshold} | Δ{(lstmMSE-lstmThreshold).toFixed(3)}</div>
              <svg viewBox="0 0 200 30" style="width:100%;height:30px;margin:2px 0">
                <line x1="0" y1={30*(1-lstmThreshold/1.5)} x2="200" y2={30*(1-lstmThreshold/1.5)} stroke={OB.red} stroke-width="0.5" stroke-dasharray="3,3"/>
                <path d={sparkPath(lstmHistory,200,30)} fill="none" stroke={lstmMSE>lstmThreshold?OB.red:OB.teal} stroke-width="1"/>
              </svg>
              <div class="lstm-pred" style="text-align:center;color:{predictiveDays<14?OB.amber:OB.green}">
                {#if predictiveDays<99}CRITICAL IN ~{predictiveDays}d{:else}STABLE TRAJECTORY{/if}
              </div>
            </div>
          </div>
          <div class="pnl" bind:this={sectionRefs['sys']}>
            <div class="ph"><h2>TWIN ENGINE STATUS</h2><span class="ptag pt-t">PROPULSION</span></div>
            <div style="padding:4px 6px">
              <div class="engine-dual">
                <div class="eng-box" class:eng-healthy={engineFaultState.port==='healthy'} class:eng-warning={engineFaultState.port==='warning'} class:eng-fault={engineFaultState.port==='fault'}>
                  <span class="eng-label">E1 — PORT</span>
                  <span class="eng-status">{engineFaultState.port.toUpperCase()}</span>
                  <span style="font:500 6px var(--mono);color:var(--n-td)">MCR {telemetry.drl_optimization.mcr_load_pct.toFixed(1)}%</span>
                  <span style="font:500 6px var(--mono);color:var(--n-td)">RPM {telemetry.engine.rpm.toFixed(0)}</span>
                </div>
                <div class="eng-box" class:eng-healthy={engineFaultState.starboard==='healthy'} class:eng-warning={engineFaultState.starboard==='warning'} class:eng-fault={engineFaultState.starboard==='fault'}>
                  <span class="eng-label">E2 — STARBOARD</span>
                  <span class="eng-status">{engineFaultState.starboard.toUpperCase()}</span>
                  <span style="font:500 6px var(--mono);color:var(--n-td)">TEMP {telemetry.engine.temperature_c.toFixed(0)}°C</span>
                  <span style="font:500 6px var(--mono);color:var(--n-td)">CPP 87.3°</span>
                </div>
              </div>
              <div class="rdts">
                <div class="ro"><span class="ro-l">Prop Sync</span><span class="ro-v ro-green">SYNCHRONIZED</span></div>
                <div class="ro"><span class="ro-l">Shaft RPM Δ</span><span class="ro-v">{(Math.abs(telemetry.engine.rpm - 120)*0.1).toFixed(2)}</span></div>
              </div>
            </div>
          </div>
          <div class="pnl">
            <div class="ph"><h2>EDGE SYSTEMS CONFIG</h2><span class="ptag pt-t">SOLAS</span></div>
            <div style="padding:4px 6px">
              <div class="solas-toggle-enhanced" class:solas-active={solasOverrideActive}>
                <span class="solas-label">⚠ SOLAS OVERRIDE</span>
                <button class="solas-btn" class:solas-armed={solasOverrideActive} onclick={()=>{solasOverrideActive=!solasOverrideActive;if(solasOverrideActive)pushAlert('SOLAS Override ARMED — Manual mode engaged','CRITICAL');}}>
                  <span class="solas-ind">{solasOverrideActive?'ARMED':'DISARMED'}</span>
                  <div class="solas-tk"><div class="solas-th" class:solas-th-on={solasOverrideActive}></div></div>
                </button>
              </div>
              <div class="net-tiers">
                <div class="net-tier active"><span class="net-tier-label">LOCAL</span><span class="net-tier-val" style="color:var(--n-green)">● ACTIVE</span></div>
                <div class="net-tier"><span class="net-tier-label">4G/LTE</span><span class="net-tier-val">○ STANDBY</span></div>
                <div class="net-tier"><span class="net-tier-label">ISRO S-BAND</span><span class="net-tier-val" style="color:var(--n-cyan)">● TRANSMITTING</span></div>
              </div>
              <div class="rdts">
                <div class="ro"><span class="ro-l">Encryption</span><span class="ro-v ro-green">AES-256 ✓</span></div>
                <div class="ro"><span class="ro-l">F1 Pipeline</span><span class="ro-v ro-teal">ACTIVE</span></div>
                <div class="ro"><span class="ro-l">Edge Latency</span><span class="ro-v">{wsLatency}ms</span></div>
              </div>
              <!-- Denoising Autoencoder Sliders -->
              <div class="denoise-panel">
                <div class="denoise-header">F1 PIPELINE: AUTOENCODER NOISE FILTER</div>
                <div class="denoise-mse">MSE: <span style="color:{OB.teal}">{(0.12 + Math.sin(totalFrames*0.005)*0.03).toFixed(3)}</span></div>
                <div class="denoise-slider-w">
                  <label class="denoise-lbl">
                    <span>Imputation Sensitivity</span><span class="denoise-pct">{imputationSens}%</span>
                    <input type="range" min="0" max="100" class="denoise-range" bind:value={imputationSens}/>
                  </label>
                  <span class="denoise-hint">Dropout threshold for missing data interpolation</span>
                </div>
                <div class="denoise-slider-w">
                  <label class="denoise-lbl">
                    <span>Smoothing Factor</span><span class="denoise-pct">{smoothingFactor}%</span>
                    <input type="range" min="0" max="100" class="denoise-range" bind:value={smoothingFactor}/>
                  </label>
                  <span class="denoise-hint">Savitzky-Golay window — k={Math.round(smoothingFactor/14.3)}, ord=3</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ── ENGINE PAGE ENHANCEMENTS (from SAMUDRA repo) ─────────── -->
        <div class="r2" style:display={currentView === 'engine' ? 'grid' : 'none'}>
          <!-- LSTM 24HR BAR CHART -->
          <div class="pnl">
            <div class="ph"><h2>LSTM 24HR ANALYSIS</h2>
              <span class="ptag" style="color:{lstmMSE>lstmThreshold?OB.red:OB.green}">
                {lstmMSE>lstmThreshold?'ANOMALY DETECTED':'STABLE'}
              </span>
            </div>
            <div style="padding:4px 6px;height:130px"><canvas bind:this={c6El}></canvas></div>
          </div>
          <!-- LIVE TELEMETRY 2×2 GRID -->
          <div class="pnl">
            <div class="ph"><h2>LIVE TELEMETRY</h2><span class="ptag pt-t">PER-ENGINE</span></div>
            <div class="telem-grid">
              <div class="telem-cell">
                <span class="telem-eng">E1 Lube Oil</span>
                <span class="telem-val">{(4.8+Math.sin(totalFrames*0.01)*0.3).toFixed(1)} bar</span>
                <span class="telem-tag telem-ok">NORMAL</span>
              </div>
              <div class="telem-cell">
                <span class="telem-eng">E1 Coolant</span>
                <span class="telem-val">{(82+Math.sin(totalFrames*0.008)*3).toFixed(0)}°C</span>
                <span class="telem-tag telem-ok">NORMAL</span>
              </div>
              <div class="telem-cell">
                <span class="telem-eng">E2 Lube Oil</span>
                <span class="telem-val">{(4.6+Math.sin(totalFrames*0.012)*0.2).toFixed(1)} bar</span>
                <span class="telem-tag telem-ok">NORMAL</span>
              </div>
              <div class="telem-cell" class:telem-alert={telemetry.engine.temperature_c>400}>
                <span class="telem-eng">E2 Exhaust C3</span>
                <span class="telem-val">{telemetry.engine.temperature_c.toFixed(0)}°C</span>
                <span class="telem-tag" class:telem-ok={telemetry.engine.temperature_c<=400} class:telem-warn={telemetry.engine.temperature_c>400}>
                  {telemetry.engine.temperature_c>400?'ALERT':'NORMAL'}
                </span>
              </div>
            </div>
          </div>
        </div>
        <!-- PROPULSION SYNC HUB -->
        <div class="pnl prop-sync-hub" style:display={currentView === 'engine' ? 'block' : 'none'}>
          <div class="ph"><h2>PROPULSION SYNC HUB</h2><span class="ptag pt-t">SYNC ACTIVE</span></div>
          <div style="padding:4px 6px">
            <div class="mcr-zone-w">
              <span class="mcr-lbl">MCR Load</span>
              <div class="mcr-bar">
                <div class="mcr-optimal" style="left:70%;width:15%"></div>
                <div class="mcr-ptr" style="left:{Math.min(100,telemetry.drl_optimization.mcr_load_pct)}%"></div>
              </div>
              <span class="mcr-val" style="color:{telemetry.drl_optimization.mcr_load_pct>=70&&telemetry.drl_optimization.mcr_load_pct<=85?OB.green:OB.amber}">{telemetry.drl_optimization.mcr_load_pct.toFixed(1)}%</span>
            </div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">CPP Pitch</span><span class="ro-v ro-green">18.4° MATCHED</span></div>
              <div class="ro"><span class="ro-l">Shaft RPM</span><span class="ro-v">{telemetry.engine.rpm.toFixed(0)} NOMINAL</span></div>
              <div class="ro"><span class="ro-l">Load Balance</span><span class="ro-v" style="color:{derived.loadBalance>90?OB.green:OB.amber}">{derived.loadBalance.toFixed(0)}%</span></div>
              <div class="ro"><span class="ro-l">Prop Coeff Δ</span><span class="ro-v">{derived.propCoeffDev.toFixed(3)}</span></div>
            </div>
          </div>
        </div>

        <!-- WIND COMPASS + STABILITY -->
        <div class="r2" style:display={currentView === 'settings' ? 'grid' : 'none'}>
          <div class="pnl"><div class="ph"><h2>WIND COMPASS</h2><span class="ptag">BFT {derived.bft}</span></div>
            <div class="compass-w">
              <svg viewBox="0 0 120 120" class="compass-svg">
                <circle cx="60" cy="60" r="50" fill="none" stroke={OB.border} stroke-width="1"/>
                <circle cx="60" cy="60" r="35" fill="none" stroke={OB.border} stroke-width=".5" stroke-dasharray="2,4"/>
                <circle cx="60" cy="60" r="20" fill="none" stroke={OB.border} stroke-width=".5" stroke-dasharray="1,3"/>
                {#each [0,45,90,135,180,225,270,315] as a}<line x1={60+48*Math.sin(a*Math.PI/180)} y1={60-48*Math.cos(a*Math.PI/180)} x2={60+52*Math.sin(a*Math.PI/180)} y2={60-52*Math.cos(a*Math.PI/180)} stroke={OB.textDim} stroke-width="1"/>{/each}
                <text x="60" y="8" text-anchor="middle" fill={OB.textSec} font-size="6" font-family="'JetBrains Mono',monospace">N</text>
                <text x="112" y="62" text-anchor="middle" fill={OB.textDim} font-size="5" font-family="'JetBrains Mono',monospace">E</text>
                <text x="60" y="116" text-anchor="middle" fill={OB.textDim} font-size="5" font-family="'JetBrains Mono',monospace">S</text>
                <text x="8" y="62" text-anchor="middle" fill={OB.textDim} font-size="5" font-family="'JetBrains Mono',monospace">W</text>
                <!-- Heading -->
                <line x1="60" y1="60" x2={60+40*Math.sin(telemetry.navigation.heading_deg*Math.PI/180)} y2={60-40*Math.cos(telemetry.navigation.heading_deg*Math.PI/180)} stroke={OB.teal} stroke-width="2" stroke-linecap="round"/>
                <!-- Wind arrow -->
                <line x1="60" y1="60" x2={60+35*Math.sin(telemetry.environment.wind_direction_deg*Math.PI/180)} y2={60-35*Math.cos(telemetry.environment.wind_direction_deg*Math.PI/180)} stroke={OB.amber} stroke-width="1.5" stroke-linecap="round" stroke-dasharray="3,2"/>
                <circle cx="60" cy="60" r="3" fill={OB.surface0} stroke={OB.teal} stroke-width="1"/>
                <text x="60" y="63" text-anchor="middle" fill={OB.textPri} font-size="4" font-family="'JetBrains Mono',monospace">{telemetry.navigation.heading_deg.toFixed(0)}°</text>
              </svg>
              <div class="compass-data">
                <div class="ro"><span class="ro-l">Heading</span><span class="ro-v">{telemetry.navigation.heading_deg.toFixed(1)}°</span></div>
                <div class="ro"><span class="ro-l">Wind Dir</span><span class="ro-v">{telemetry.environment.wind_direction_deg.toFixed(0)}°</span></div>
                <div class="ro"><span class="ro-l">Rel Wind</span><span class="ro-v">{derived.relWindDeg.toFixed(0)}°</span></div>
                <div class="ro"><span class="ro-l">Wind Spd</span><span class="ro-v">{telemetry.environment.wind_speed_kts.toFixed(0)} kts</span></div>
                <div class="ro"><span class="ro-l">Beaufort</span><span class="ro-v">BFT {derived.bft}</span></div>
              </div>
            </div>
          </div>
          <div class="pnl"><div class="ph"><h2>STABILITY INDICATORS</h2><span class="ptag">INTACT</span></div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">Pitch</span><span class="ro-v" style="color:{Math.abs(telemetry.physics.pitch_deg)>5?OB.red:OB.textSec}">{telemetry.physics.pitch_deg.toFixed(2)}°</span><div class="ro-bar"><div class="ro-bf" style="width:{Math.min(100,Math.abs(telemetry.physics.pitch_deg)*10)}%;background:{Math.abs(telemetry.physics.pitch_deg)>5?OB.red:OB.green}"></div></div></div>
              <div class="ro"><span class="ro-l">Roll</span><span class="ro-v" style="color:{Math.abs(telemetry.physics.roll_deg)>8?OB.red:OB.textSec}">{telemetry.physics.roll_deg.toFixed(2)}°</span><div class="ro-bar"><div class="ro-bf" style="width:{Math.min(100,Math.abs(telemetry.physics.roll_deg)*6)}%;background:{Math.abs(telemetry.physics.roll_deg)>8?OB.red:OB.green}"></div></div></div>
              <div class="ro"><span class="ro-l">Trim Fuel Δ</span><span class="ro-v">{telemetry.physics.trim_fuel_penalty_pct.toFixed(1)}%</span></div>
              <div class="ro"><span class="ro-l">Wave Height</span><span class="ro-v">{telemetry.environment.wave_height_m.toFixed(2)} m</span></div>
              <div class="ro"><span class="ro-l">Sea State</span><span class="ro-v">SS{telemetry.environment.sea_state.toFixed(0)}</span></div>
              <div class="ro"><span class="ro-l">GM (est)</span><span class="ro-v">{(1.2 - Math.abs(telemetry.physics.roll_deg)*0.02).toFixed(2)} m</span></div>
              <div class="ro"><span class="ro-l">Struct Risk</span><span class="ro-v" style="color:{riskColor(derived.risk.structural)}">{derived.risk.structural.toFixed(0)}/100</span><div class="ro-bar"><div class="ro-bf" style="width:{derived.risk.structural}%;background:{riskColor(derived.risk.structural)}"></div></div></div>
            </div>
          </div>
        </div>

        <!-- ═══════ PHASE 4: 7-GAP INTELLIGENCE MODULES ═══════════════════ -->
        <!-- SENSOR INTEGRATION + DATA QUALITY (Tactical / Engine) -->
        <div class="r2" style:display={currentView === 'tactical' || currentView === 'engine' ? 'grid' : 'none'}>
          <div class="pnl">
            <div class="ph"><h2>📡 SENSOR INTEGRATION HUB</h2>
              <span class="ptag pt-t">IHO S-57</span>
              <span class="ptag" style="color:{derived.sensorHealthPct>=90?OB.green:derived.sensorHealthPct>=70?OB.amber:OB.red};background:rgba({derived.sensorHealthPct>=90?'34,255,136':derived.sensorHealthPct>=70?'255,170,51':'255,51,68'},.08)">{derived.sensorHealthPct.toFixed(0)}% HEALTH</span>
            </div>
            <div class="rdts">
              {#each ['ECDIS','EMCS','FOMS','WEATHER','VDR'] as sname}
              {@const sdata = (telemetry.sensor_integration?.sensors ?? {})[sname.toLowerCase()] ?? {}}
              <div class="ro">
                <span class="ro-l">{sname}</span>
                <span class="ro-v" style="color:{sdata.status==='OK'||sdata.status==='NOMINAL'?OB.green:sdata.status==='DEGRADED'?OB.amber:OB.red}">{sdata.status ?? 'N/A'}</span>
                <span style="font:500 6px var(--mono);color:var(--n-td)">{sdata.update_rate_hz?.toFixed(1) ?? '—'} Hz</span>
              </div>
              {/each}
              <div class="ro"><span class="ro-l">UKC</span><span class="ro-v ro-cyan">{(telemetry.sensor_integration?.sensors?.ecdis?.ukc_m ?? 0).toFixed(1)} m</span></div>
              <div class="ro"><span class="ro-l">XTE</span><span class="ro-v">{(telemetry.sensor_integration?.sensors?.ecdis?.xte_nm ?? 0).toFixed(3)} nm</span></div>
              <div class="ro"><span class="ro-l">Fuel Quality</span><span class="ro-v">{telemetry.sensor_integration?.sensors?.foms?.fuel_quality ?? 'ISO 8217'}</span></div>
            </div>
          </div>
          <div class="pnl">
            <div class="ph"><h2>📊 DATA ARCHITECTURE</h2>
              <span class="ptag pt-t">UNIFIED BUS</span>
              <span class="ptag" style="color:{derived.dqiScore>=0.9?OB.green:derived.dqiScore>=0.7?OB.amber:OB.red};background:rgba({derived.dqiScore>=0.9?'34,255,136':derived.dqiScore>=0.7?'255,170,51':'255,51,68'},.08)">DQI {(derived.dqiScore*100).toFixed(0)}%</span>
            </div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">Bus Rate</span><span class="ro-v ro-teal">{derived.busMessageRate.toFixed(0)} msg/s</span></div>
              <div class="ro"><span class="ro-l">Completeness</span><span class="ro-v">{((telemetry.data_architecture?.quality?.completeness ?? 1)*100).toFixed(0)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{(telemetry.data_architecture?.quality?.completeness ?? 1)*100}%;background:{OB.teal}"></div></div></div>
              <div class="ro"><span class="ro-l">Timeliness</span><span class="ro-v">{((telemetry.data_architecture?.quality?.timeliness ?? 1)*100).toFixed(0)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{(telemetry.data_architecture?.quality?.timeliness ?? 1)*100}%;background:{OB.cyan}"></div></div></div>
              <div class="ro"><span class="ro-l">Accuracy</span><span class="ro-v">{((telemetry.data_architecture?.quality?.accuracy ?? 1)*100).toFixed(0)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{(telemetry.data_architecture?.quality?.accuracy ?? 1)*100}%;background:{OB.green}"></div></div></div>
              <div class="ro"><span class="ro-l">Consistency</span><span class="ro-v">{((telemetry.data_architecture?.quality?.consistency ?? 1)*100).toFixed(0)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{(telemetry.data_architecture?.quality?.consistency ?? 1)*100}%;background:{OB.purple}"></div></div></div>
              <div class="ro"><span class="ro-l">NMEA Parsed</span><span class="ro-v">{telemetry.data_architecture?.nmea_parsed ?? 0}</span></div>
              <div class="ro"><span class="ro-l">Registered Sensors</span><span class="ro-v">{telemetry.data_architecture?.registry_count ?? 10}</span></div>
            </div>
          </div>
        </div>

        <!-- PREDICTIVE MAINTENANCE + HULL/PROPULSION (Engine view) -->
        <div class="r2" style:display={currentView === 'engine' || currentView === 'tactical' ? 'grid' : 'none'}>
          <div class="pnl">
            <div class="ph"><h2>🔧 PREDICTIVE MAINTENANCE</h2>
              <span class="ptag" style="color:{derived.anomalyCount>0?OB.red:OB.green};background:rgba({derived.anomalyCount>0?'255,51,68':'34,255,136'},.08)">{derived.anomalyCount>0?'ALERT':'NOMINAL'}</span>
              <span class="ptag pt-t">MIL-STD-3034</span>
            </div>
            <div class="rdts">
              {#each Object.entries(telemetry.predictive_maintenance?.components ?? {}) as [cname, cdata]}
              {@const cd = cdata as any}
              <div class="ro">
                <span class="ro-l" style="text-transform:capitalize">{cname.replace(/_/g,' ')}</span>
                <span class="ro-v" style="color:{cd.health_tier>=4?OB.green:cd.health_tier>=3?OB.teal:cd.health_tier>=2?OB.amber:OB.red}">T{cd.health_tier ?? 5}</span>
                <span style="font:500 6px var(--mono);color:var(--n-td)">RUL {((cd.rul_hours ?? 0)/24).toFixed(0)}d</span>
                <div class="ro-bar"><div class="ro-bf" style="width:{(cd.health_pct ?? 100)}%;background:{heatColor(1-(cd.health_pct ?? 100)/100)}"></div></div>
              </div>
              {/each}
              <div class="ro"><span class="ro-l">Anomalies</span><span class="ro-v" style="color:{derived.anomalyCount>0?OB.red:OB.green}">{derived.anomalyCount}</span></div>
              <div class="ro"><span class="ro-l">Next Maint</span><span class="ro-v ro-amber">{derived.maintenanceDue.toFixed(0)} h</span></div>
              <div class="ro"><span class="ro-l">Avg RUL</span><span class="ro-v" style="color:{derived.avgRULDays<30?OB.red:derived.avgRULDays<90?OB.amber:OB.green}">{derived.avgRULDays.toFixed(0)} days</span></div>
            </div>
          </div>
          <div class="pnl">
            <div class="ph"><h2>🛥 HULL & HYBRID PROPULSION</h2>
              <span class="ptag pt-t">ISO 19030</span>
              <span class="ptag" style="color:{OB.cyan};background:rgba(0,200,255,.08)">{derived.propMode}</span>
            </div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">Coating Age</span><span class="ro-v">{derived.hullCoatingAge} mo</span></div>
              <div class="ro"><span class="ro-l">ΔR/R Fouling</span><span class="ro-v" style="color:{derived.hullDeltaRR>10?OB.red:derived.hullDeltaRR>5?OB.amber:OB.green}">{derived.hullDeltaRR.toFixed(1)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{Math.min(100,derived.hullDeltaRR*5)}%;background:{derived.hullDeltaRR>10?OB.red:derived.hullDeltaRR>5?OB.amber:OB.green}"></div></div></div>
              <div class="ro"><span class="ro-l">Coating Type</span><span class="ro-v">{telemetry.hull_propulsion?.coating?.type ?? 'SPC'}</span></div>
              <div class="ro"><span class="ro-l">Clean ROI</span><span class="ro-v ro-green">${(telemetry.hull_propulsion?.cleaning_roi?.annual_savings ?? 0).toFixed(0)}/yr</span></div>
              <div class="ro" style="border-top:1px solid var(--n-b);margin-top:2px;padding-top:2px"><span class="ro-l" style="font-weight:700;color:var(--n-ts)">CODLAG HYBRID</span></div>
              <div class="ro"><span class="ro-l">Battery SOC</span><span class="ro-v" style="color:{derived.batterySOC>50?OB.green:derived.batterySOC>20?OB.amber:OB.red}">{derived.batterySOC.toFixed(0)}%</span><div class="ro-bar"><div class="ro-bf" style="width:{derived.batterySOC}%;background:{derived.batterySOC>50?OB.green:derived.batterySOC>20?OB.amber:OB.red}"></div></div></div>
              <div class="ro"><span class="ro-l">Motor Power</span><span class="ro-v">{(telemetry.hull_propulsion?.hybrid?.motor_kw ?? 0).toFixed(0)} kW</span></div>
              <div class="ro"><span class="ro-l">Fuel Saving</span><span class="ro-v ro-green">{(telemetry.hull_propulsion?.hybrid?.fuel_saving_pct ?? 0).toFixed(1)}%</span></div>
            </div>
          </div>
        </div>

        <!-- BLIND SPOTS + HUMAN-AI (Engine / Settings) -->
        <div class="r2" style:display={currentView === 'engine' || currentView === 'settings' ? 'grid' : 'none'}>
          <div class="pnl">
            <div class="ph"><h2>🔍 SYSTEMIC BLIND SPOTS</h2>
              <span class="ptag" style="color:{derived.blindSpotRisk>60?OB.red:derived.blindSpotRisk>30?OB.amber:OB.green};background:rgba({derived.blindSpotRisk>60?'255,51,68':derived.blindSpotRisk>30?'255,170,51':'34,255,136'},.08)">RISK {derived.blindSpotRisk.toFixed(0)}</span>
            </div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">CUSUM Drift</span><span class="ro-v" style="color:{derived.degradationDrift>5?OB.red:derived.degradationDrift>2?OB.amber:OB.green}">{derived.degradationDrift.toFixed(2)}</span><div class="ro-bar"><div class="ro-bf" style="width:{Math.min(100,derived.degradationDrift*10)}%;background:{derived.degradationDrift>5?OB.red:OB.amber}"></div></div></div>
              <div class="ro"><span class="ro-l">Micro-Climate</span><span class="ro-v">{telemetry.blind_spots?.micro_climate?.zone ?? 'Open Sea'}</span></div>
              <div class="ro"><span class="ro-l">KE Spike</span><span class="ro-v" style="color:{(telemetry.blind_spots?.kinetic_spike?.detected ?? false)?OB.red:OB.green}">{(telemetry.blind_spots?.kinetic_spike?.detected ?? false)?'DETECTED':'CLEAR'}</span></div>
              <div class="ro"><span class="ro-l">Sync Status</span><span class="ro-v">{(telemetry.blind_spots?.sync?.all_synced ?? true)?'ALL SYNCED':'DRIFT'}</span></div>
              <div class="ro"><span class="ro-l">Causal Top</span><span class="ro-v ro-cyan">{telemetry.blind_spots?.causal?.top_cause ?? 'N/A'}</span></div>
              <div class="ro"><span class="ro-l">Variance Ratio</span><span class="ro-v">{(telemetry.blind_spots?.causal?.variance_ratio ?? 0).toFixed(2)}</span></div>
            </div>
          </div>
          <div class="pnl">
            <div class="ph"><h2>🤝 HUMAN-AI COLLABORATION</h2>
              <span class="ptag" style="color:{derived.aiConfidence==='HIGH'?OB.green:derived.aiConfidence==='MEDIUM'?OB.amber:OB.red};background:rgba({derived.aiConfidence==='HIGH'?'34,255,136':derived.aiConfidence==='MEDIUM'?'255,170,51':'255,51,68'},.08)">{derived.aiConfidence} CONF</span>
              <span class="ptag pt-t">SOLAS</span>
            </div>
            <div class="rdts">
              <div class="ro"><span class="ro-l">Confidence</span><span class="ro-v" style="color:{derived.aiConfidence==='HIGH'?OB.green:derived.aiConfidence==='MEDIUM'?OB.amber:OB.red}">{derived.aiConfidence}</span></div>
              <div class="ro"><span class="ro-l">Connectivity</span><span class="ro-v ro-cyan">{derived.connectivityType}</span></div>
              <div class="ro"><span class="ro-l">Bandwidth</span><span class="ro-v">{(telemetry.human_ai_collaboration?.connectivity?.bandwidth_kbps ?? 0).toFixed(0)} kbps</span></div>
              <div class="ro"><span class="ro-l">SHAP Top Factor</span><span class="ro-v ro-purple">{derived.shapTopFactor}</span></div>
              <div class="ro"><span class="ro-l">Dist Shift</span><span class="ro-v" style="color:{(telemetry.human_ai_collaboration?.distribution_shift?.detected ?? false)?OB.red:OB.green}">{(telemetry.human_ai_collaboration?.distribution_shift?.detected ?? false)?'DETECTED':'STABLE'}</span></div>
              <div class="ro"><span class="ro-l">Override</span><span class="ro-v" style="color:{solasOverrideActive?OB.red:OB.green}">{solasOverrideActive?'ARMED':'SAFE'}</span></div>
              <div class="ro"><span class="ro-l">Advisory</span><span class="ro-v" style="font-size:6px">{telemetry.human_ai_collaboration?.explainability?.nl_advisory ?? 'Nominal'}</span></div>
            </div>
          </div>
        </div>

        <!-- EEXI COMPLIANCE (Compliance view) -->
        <div class="pnl" style:display={currentView === 'compliance' || currentView === 'tactical' ? 'block' : 'none'}>
          <div class="ph hero-ph"><h2>⚖ EEXI COMPLIANCE ENGINE</h2>
            <span class="ptag pt-t">MEPC.328(76)</span>
            <span class="ptag" style="color:{derived.eexiCompliant?OB.green:OB.red};background:rgba({derived.eexiCompliant?'34,255,136':'255,51,68'},.12)">{derived.eexiCompliant?'COMPLIANT':'NON-COMPLIANT'}</span>
            <span class="ptag">CII {derived.ciiEnhancedRating}</span>
          </div>
          <div class="eexi-grid">
            <div class="eexi-card">
              <span class="eexi-label">EEXI ATTAINED</span>
              <span class="eexi-big" style="color:{derived.eexiCompliant?OB.green:OB.red}">{derived.eexiAttained.toFixed(2)}</span>
              <span class="eexi-unit">gCO₂/t·nm</span>
            </div>
            <div class="eexi-card">
              <span class="eexi-label">EEXI REQUIRED</span>
              <span class="eexi-big" style="color:{OB.teal}">{derived.eexiRequired.toFixed(2)}</span>
              <span class="eexi-unit">gCO₂/t·nm</span>
            </div>
            <div class="eexi-card">
              <span class="eexi-label">MARGIN</span>
              <span class="eexi-big" style="color:{derived.eexiRequired>0?((derived.eexiRequired-derived.eexiAttained)/derived.eexiRequired*100>0?OB.green:OB.red):OB.textSec}">{derived.eexiRequired>0?((derived.eexiRequired-derived.eexiAttained)/derived.eexiRequired*100).toFixed(1):'—'}%</span>
              <span class="eexi-unit">buffer</span>
            </div>
            <div class="eexi-card">
              <span class="eexi-label">CII RATING</span>
              <span class="eexi-big" style="color:{ciiColor(derived.ciiEnhancedRating)}">{derived.ciiEnhancedRating}</span>
              <span class="eexi-unit">2023-2030</span>
            </div>
          </div>
          <div class="rdts" style="padding:2px 6px">
            <div class="ro"><span class="ro-l">CF (HFO)</span><span class="ro-v">{CARBON_FACTOR}</span></div>
            <div class="ro"><span class="ro-l">SFC</span><span class="ro-v">185 g/kWh</span></div>
            <div class="ro"><span class="ro-l">MCR</span><span class="ro-v">{DESIGN_POWER_KW} kW</span></div>
            <div class="ro"><span class="ro-l">DWT</span><span class="ro-v">2,350 t</span></div>
            <div class="ro"><span class="ro-l">EPL Applied</span><span class="ro-v" style="color:{(telemetry.eexi_compliance?.eexi?.epl_applied ?? false)?OB.green:OB.textDim}">{(telemetry.eexi_compliance?.eexi?.epl_applied ?? false)?'YES':'NO'}</span></div>
            <div class="ro"><span class="ro-l">IMO DCS</span><span class="ro-v ro-teal">MEPC.278(70)</span></div>
            <div class="ro"><span class="ro-l">Annual Reduction</span><span class="ro-v">{(telemetry.eexi_compliance?.cii_tracker?.annual_reduction_pct ?? 2).toFixed(1)}%</span></div>
          </div>
        </div>

        <!-- STATUS BAR -->
        <div class="sbar">
          <span class="sb"><span class="sbd" class:sb-on={connected}></span> WS {connected?'ONLINE':'OFFLINE'}</span>
          <span class="sb">FPS {fps}</span>
          <span class="sb">FRAMES {totalFrames}</span>
          <span class="sb">LAT {wsLatency}ms</span>
          <span class="sb">AI {aiEnabled?'ON':'OFF'}</span>
          <span class="sb">MISSION {telemetry.cii_segregation.mission_state}</span>
          <span class="sb" style="color:{riskColor(derived.risk.overall)}">RISK {riskLabel(derived.risk.overall)}</span>
          <span class="sb">FUEL {(derived.fuelRemainKg/1000).toFixed(0)}t</span>
          <span class="sb">ENDURE {derived.endDays.toFixed(1)}d</span>
          <span class="sb">CII {telemetry.cii_segregation.cii_rating_corrected}</span>
          <span class="sb" style="color:{OB.textDim}">SAMUDRA v4.0</span>
        </div>
      </div>

      <!-- ── ALERTS SIDEBAR ────────────────────────────────────────────── -->
      <div class="ac">
        <div class="pnl ap"><div class="ph"><h2>⚡ SYSTEM ALERTS</h2><span class="acnt">{alerts.length}</span></div>
          <div class="asum">
            <span class="asb as-c">{alerts.filter(a=>a.severity==='CRITICAL').length} C</span>
            <span class="asb as-w">{alerts.filter(a=>a.severity==='WARNING').length} W</span>
            <span class="asb as-a">{alerts.filter(a=>a.severity==='ADVISORY').length} A</span>
            <span class="asb as-i">{alerts.filter(a=>a.severity==='INFO').length} I</span>
          </div>
          <div class="alist">
            {#each alerts.slice(0,40) as al (al.id)}
            <div class="ali ali-{al.severity.toLowerCase()}">
              <div class="ali-t"><span class="ali-ic">{sevIcon(al.severity)}</span><span class="ali-sv">{al.severity.slice(0,4)}</span>{#if al.count>1}<span class="ali-ct">×{al.count}</span>{/if}<span class="ali-tm">{al.time}</span></div>
              <span class="ali-msg">{al.message}</span>
            </div>
            {/each}
            {#if alerts.length === 0}<div class="ae">No alerts</div>{/if}
          </div>
        </div>
        <div class="pnl dp"><div class="ph"><h2>DIAGNOSTICS</h2></div>
          <div class="rdts">
            <div class="ro"><span class="ro-l">WS State</span><span class="ro-v">{connected?'CONNECTED':'DISCONNECTED'}</span></div>
            <div class="ro"><span class="ro-l">Frame Rate</span><span class="ro-v">{fps} Hz</span></div>
            <div class="ro"><span class="ro-l">Total Frames</span><span class="ro-v">{totalFrames}</span></div>
            <div class="ro"><span class="ro-l">Reconnects</span><span class="ro-v">{reconnectAttempts}</span></div>
            <div class="ro"><span class="ro-l">WS Latency</span><span class="ro-v">{wsLatency}ms</span></div>
            <div class="ro"><span class="ro-l">Alert Count</span><span class="ro-v">{alerts.length}</span></div>
            <div class="ro"><span class="ro-l">AI Mode</span><span class="ro-v" style="color:{aiEnabled?OB.green:OB.red}">{aiEnabled?'ENABLED':'DISABLED'}</span></div>
            <div class="ro"><span class="ro-l">Sparkline Buf</span><span class="ro-v">{sparkSOG.length}/{SPARK_LEN}</span></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
{:else}
<div class="ld"><div class="ld-ring"><div></div><div></div><div></div></div><div class="ld-txt">SAMUDRA TACTICAL COMMAND v4.0</div><div class="ld-sub">Establishing telemetry link...</div></div>
{/if}

<!-- ═══════ STYLES ═══════════════════════════════════════════════════════ -->
<style>
  :global(:root){
    --n-bg:#050810;--n-s0:#060a10;--n-s1:#0a1018;--n-s2:#101820;--n-s3:#182030;
    --n-b:#162030;--n-bh:#203040;
    --n-tp:#d0dae6;--n-ts:#7a8fa4;--n-td:#3a4a5a;
    --n-teal:#00ffcc;--n-cyan:#00c8ff;--n-amber:#ffaa33;--n-red:#ff3344;--n-green:#22ff88;--n-purple:#b06cff;--n-blue:#4499ff;--n-mag:#ff44aa;
    --mono:'JetBrains Mono','Fira Code','Consolas',monospace;--sans:'Inter','Segoe UI',system-ui,sans-serif;
  }
  :global(body){margin:0;padding:0;background:var(--n-bg);color:var(--n-tp);font-family:var(--sans);-webkit-font-smoothing:antialiased;overflow:hidden;height:100vh;}
  :global(*){box-sizing:border-box;}
  :global(::-webkit-scrollbar){width:3px;}:global(::-webkit-scrollbar-track){background:var(--n-s0);}:global(::-webkit-scrollbar-thumb){background:var(--n-b);border-radius:2px;}

  .scan-ol{position:fixed;inset:0;pointer-events:none;z-index:9999;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,204,.008) 2px,rgba(0,255,204,.008) 4px);}
  .shell{display:grid;grid-template-columns:40px 1fr;height:100vh;overflow:hidden;}

  /* NAV */
  .snav{background:var(--n-s0);border-right:1px solid var(--n-b);display:flex;flex-direction:column;align-items:center;padding:4px 0;gap:1px;z-index:100;}
  .nb{height:52px;display:flex;align-items:center;justify-content:center;padding:4px 2px;}
  .nd{width:20px;height:1px;background:var(--n-b);margin:2px 0;}
  .ni{background:none;border:none;color:var(--n-td);cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:0px;padding:3px 1px;border-radius:3px;width:34px;transition:all .15s;font-size:inherit;}
  .ni:hover{color:var(--n-ts);background:var(--n-s2);}
  .ni.active{color:var(--n-teal);background:var(--n-s2);border-left:2px solid var(--n-teal);box-shadow:inset 3px 0 8px -3px rgba(0,255,204,.15);}
  .ni-i{font-size:11px;}.ni-l{font:600 6px var(--mono);letter-spacing:.06em;}
  .ns{flex:1;}
  .nst{display:flex;flex-direction:column;align-items:center;gap:1px;padding:4px 0;}
  .cd{width:5px;height:5px;border-radius:50%;background:var(--n-red);transition:all .3s;}
  .cd.online{background:var(--n-green);box-shadow:0 0 6px var(--n-green),0 0 12px rgba(34,255,136,.3);}
  .cl{font:600 6px var(--mono);color:var(--n-td);}.cf{font:600 6px var(--mono);color:var(--n-td);}

  .vp{overflow-y:auto;overflow-x:hidden;padding:0;}

  /* TICKER */
  .ticker{height:18px;background:var(--n-s0);border-bottom:1px solid var(--n-b);overflow:hidden;position:relative;}
  .ticker-track{display:flex;gap:16px;white-space:nowrap;animation:tickScroll 40s linear infinite;font:600 8px var(--mono);}
  .tk-seg{padding:2px 0;}
  .tk-teal{color:var(--n-teal);}.tk-cyan{color:var(--n-cyan);}.tk-amber{color:var(--n-amber);}.tk-red{color:var(--n-red);}.tk-green{color:var(--n-green);}.tk-purple{color:var(--n-purple);}
  @keyframes tickScroll{0%{transform:translateX(0);}100%{transform:translateX(-50%);}}

  /* KPI */
  .kpi-r{display:flex;align-items:center;gap:0;padding:0 4px;height:44px;background:var(--n-s0);border-bottom:1px solid var(--n-b);overflow-x:auto;flex-wrap:nowrap;}
  .kg{display:flex;flex-direction:column;padding-right:6px;border-right:1px solid var(--n-b);margin-right:4px;min-width:68px;}
  .kt{font:700 10px var(--mono);color:var(--n-teal);letter-spacing:.08em;text-shadow:0 0 6px rgba(0,255,204,.3);}
  .ks{font:500 5.5px var(--sans);color:var(--n-td);letter-spacing:.04em;}
  .k{display:flex;flex-direction:column;padding:1px 5px;min-width:52px;border-right:1px solid rgba(22,32,48,.6);}
  .kl{font:600 6px var(--mono);color:var(--n-td);letter-spacing:.06em;display:flex;align-items:center;gap:2px;}
  .ktr{font-size:6px;}.ktr-up{color:var(--n-green);}.ktr-down{color:var(--n-red);}.ktr-flat{color:var(--n-td);}
  .kv{font:700 11px var(--mono);color:var(--n-tp);line-height:1.1;}
  .kv small{font-weight:400;color:var(--n-td);font-size:7px;}
  .ks-v{width:44px;height:10px;margin-top:0px;}
  .kclk{margin-left:auto;display:flex;flex-direction:column;align-items:flex-end;padding-left:6px;border-left:1px solid var(--n-b);min-width:60px;}
  .kc-utc{font:700 11px var(--mono);color:var(--n-tp);}.kc-l{font:600 6px var(--mono);color:var(--n-td);}.kc-m{font:500 8px var(--mono);color:var(--n-teal);}

  /* VOYAGE */
  .voy{display:flex;align-items:center;gap:6px;padding:2px 8px;background:var(--n-s1);border-bottom:1px solid var(--n-b);font:500 7px var(--mono);}
  .voy-l{color:var(--n-td);font-weight:700;font-size:6px;letter-spacing:.1em;}
  .voy-tk{flex:1;height:4px;background:var(--n-s3);border-radius:2px;position:relative;}
  .voy-f{height:100%;background:linear-gradient(90deg,var(--n-teal),var(--n-cyan));border-radius:2px;transition:width .5s;box-shadow:0 0 4px rgba(0,255,204,.3);}
  .voy-wp{position:absolute;top:-1.5px;width:4px;height:7px;border-radius:1px;background:var(--n-b);transform:translateX(-50%);}
  .voy-wp.passed{background:var(--n-teal);}.voy-wp.cur{background:var(--n-amber);box-shadow:0 0 4px var(--n-amber);}
  .voy-pct{color:var(--n-teal);font-weight:700;}.voy-info{color:var(--n-ts);}.voy-eta{color:var(--n-td);}

  /* ALERT BANNERS */
  .ab{display:flex;align-items:center;gap:4px;padding:2px 8px;font:600 7px var(--mono);letter-spacing:.03em;}
  .ab-crit{background:rgba(255,51,68,.08);border-bottom:1px solid rgba(255,51,68,.2);color:var(--n-red);animation:critPulse 2s infinite;}
  .ab-ghost{background:rgba(176,108,255,.06);border-bottom:1px solid rgba(176,108,255,.15);color:var(--n-purple);animation:ghostPulse 2s infinite;}
  .ab-warn{background:rgba(255,170,51,.06);border-bottom:1px solid rgba(255,170,51,.15);color:var(--n-amber);}
  .ab-off{background:rgba(255,51,68,.04);border-bottom:1px solid rgba(255,51,68,.1);color:var(--n-td);}
  .ab-i{font-size:9px;}.ab-t{flex:1;}

  /* OVERRIDE */
  .ovr{padding:2px 8px;background:var(--n-s1);border-bottom:1px solid var(--n-b);}
  .ovr-h{display:flex;align-items:center;gap:6px;}
  .ovr-i{font-size:9px;color:var(--n-amber);}.ovr-t{font:700 7px var(--mono);color:var(--n-amber);letter-spacing:.08em;text-shadow:0 0 4px rgba(255,170,51,.2);}
  .ovr-sp{flex:1;}.ovr-sub{font:500 7px var(--mono);color:var(--n-td);}
  .ovr-btn{background:none;border:none;cursor:pointer;display:flex;align-items:center;gap:4px;padding:1px;}
  .tog-tk{width:24px;height:12px;border-radius:6px;position:relative;transition:background .2s;}
  .on .tog-tk{background:rgba(0,255,204,.25);}.off .tog-tk{background:rgba(255,51,68,.25);}
  .tog-th{position:absolute;top:1.5px;width:9px;height:9px;border-radius:50%;transition:all .2s;}
  .on .tog-th{left:13px;background:var(--n-teal);box-shadow:0 0 4px var(--n-teal);}.off .tog-th{left:1.5px;background:var(--n-red);}
  .tog-s{font:700 7px var(--mono);}.on .tog-s{color:var(--n-teal);}.off .tog-s{color:var(--n-red);}

  /* CONTENT */
  .page-title-bar{display:flex;align-items:center;gap:6px;padding:3px 8px;background:linear-gradient(90deg,var(--n-s0),rgba(0,255,204,.03),var(--n-s0));border-bottom:1px solid rgba(0,255,204,.15);}
  .pt-icon{font-size:12px;filter:drop-shadow(0 0 4px rgba(0,255,204,.3));}
  .pt-name{font:700 10px var(--mono);color:var(--n-teal);letter-spacing:.1em;margin:0;text-shadow:0 0 8px rgba(0,255,204,.25);}
  .pt-fkey{font:600 7px var(--mono);color:var(--n-td);background:var(--n-s3);padding:1px 4px;border-radius:2px;border:1px solid var(--n-b);}
  .pt-sep{flex:1;}
  .pt-ai{font:700 7px var(--mono);padding:1px 6px;border-radius:2px;letter-spacing:.06em;}
  .pt-ai-on{color:var(--n-green);background:rgba(34,255,136,.08);border:1px solid rgba(34,255,136,.2);}
  .pt-ai-off{color:var(--n-red);background:rgba(255,51,68,.08);border:1px solid rgba(255,51,68,.2);}
  .pt-vessel{font:600 7px var(--mono);color:var(--n-ts);background:var(--n-s2);padding:1px 4px;border-radius:2px;}
  .pt-band{font:500 6px var(--mono);color:var(--n-td);}
  .content{display:grid;grid-template-columns:1fr 170px;gap:0;}
  .mc{padding:3px;display:flex;flex-direction:column;gap:3px;}

  /* GAUGE STRIP */
  .gs{display:flex;gap:2px;flex-wrap:wrap;}
  .gc{background:var(--n-s1);border:1px solid var(--n-b);border-radius:3px;padding:2px;display:flex;flex-direction:column;align-items:center;min-width:56px;flex:1;}
  .gsvg{width:48px;height:48px;}
  .gc-tk{justify-content:center;padding:3px 6px;border-left:2px solid var(--n-green);}
  .tk-v{font:700 14px var(--mono);color:var(--n-green);text-shadow:0 0 8px rgba(34,255,136,.3);}.tk-u{font:500 6px var(--mono);color:var(--n-td);}.tk-r{font:600 7px var(--mono);color:var(--n-teal);}

  /* FUEL STRIP */
  .fas{display:flex;gap:1px;flex-wrap:wrap;background:var(--n-s1);border:1px solid var(--n-b);border-radius:3px;padding:2px 4px;}
  .fi{flex:1;min-width:62px;display:flex;flex-direction:column;padding:1px 3px;border-right:1px solid rgba(22,32,48,.4);}
  .fi:last-child{border-right:none;}
  .fi-l{font:600 5px var(--mono);color:var(--n-td);letter-spacing:.06em;text-transform:uppercase;}
  .fi-v{font:700 9px var(--mono);color:var(--n-tp);}
  .fi-v small{font-weight:400;color:var(--n-td);font-size:7px;}
  .fi-b{height:2px;background:var(--n-s3);border-radius:1px;margin-top:1px;}
  .fi-bf{height:100%;border-radius:1px;transition:width .3s;}

  /* PANELS */
  .pnl{background:var(--n-s1);border:1px solid var(--n-b);border-radius:3px;overflow:hidden;}
  .ph{display:flex;align-items:center;gap:4px;padding:3px 6px;background:var(--n-s0);border-bottom:1px solid var(--n-b);flex-wrap:wrap;}
  .ph h2{font:600 8px var(--mono);color:var(--n-ts);letter-spacing:.05em;margin:0;white-space:nowrap;}
  .ptag{font:600 6px var(--mono);padding:1px 4px;border-radius:2px;background:var(--n-s3);color:var(--n-td);letter-spacing:.04em;}
  .pt-t{color:var(--n-teal);background:rgba(0,255,204,.08);}
  .pt-w{color:var(--n-amber);background:rgba(255,170,51,.08);}
  .pt-gh{color:var(--n-purple);background:rgba(176,108,255,.12);animation:ghostPulse 2s infinite;}
  .ghost-glow{border-color:rgba(176,108,255,.3);box-shadow:0 0 10px rgba(176,108,255,.1);}
  .badge-transit{color:var(--n-teal)!important;background:rgba(0,255,204,.1)!important;}
  .badge-loiter{color:var(--n-amber)!important;background:rgba(255,170,51,.1)!important;}

  /* ROWS */
  .r2{display:grid;grid-template-columns:1fr 1fr;gap:3px;}
  .r4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:3px;}

  /* CHART */
  .cp .cw{padding:2px 4px 1px;height:160px;}

  /* HULL */
  .hw{height:140px;position:relative;}.hw canvas{width:100%;height:100%;display:block;}
  .hst{display:flex;gap:6px;justify-content:center;padding:2px;font:500 6px var(--mono);color:var(--n-td);border-top:1px solid var(--n-b);}

  /* MAP */
  .mw{height:140px;}.nmea{font:400 6px var(--mono);color:var(--n-td);padding:1px 4px;background:var(--n-s0);border-top:1px solid var(--n-b);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}

  /* HERO ROW */
  .r2-hero{display:grid;grid-template-columns:1fr 1fr;gap:3px;}
  .hero-pnl{border:1px solid rgba(0,255,204,.15);box-shadow:0 0 20px rgba(0,255,204,.04),inset 0 0 30px rgba(0,200,255,.02);position:relative;overflow:hidden;}
  .hero-ph{background:linear-gradient(90deg,var(--n-s0),rgba(0,255,204,.03),var(--n-s0));border-bottom:1px solid rgba(0,255,204,.15);}
  .hero-ph h2{color:var(--n-teal);text-shadow:0 0 8px rgba(0,255,204,.25);font-size:9px;}
  .hw-hero{height:380px;position:relative;overflow:hidden;}
  .hw-hero canvas{width:100%;height:100%;display:block;}
  .hull-overlay{position:absolute;top:6px;left:6px;display:flex;flex-direction:column;gap:1px;pointer-events:none;z-index:2;}
  .hull-ol-row{display:flex;gap:4px;align-items:center;}
  .hull-ol-label{font:600 6px var(--mono);color:var(--n-td);letter-spacing:.06em;min-width:36px;}
  .hull-ol-val{font:700 8px var(--mono);color:var(--n-teal);text-shadow:0 0 4px rgba(0,255,204,.3);}
  .hull-advisory{position:absolute;bottom:4px;left:6px;right:6px;pointer-events:none;z-index:2;}
  .ha-title{font:700 6px var(--mono);color:var(--n-td);letter-spacing:.08em;margin-bottom:1px;}
  .ha-item{font:500 7px var(--mono);padding:2px 4px;border-radius:2px;}
  .ha-warn{background:rgba(255,170,51,.1);color:var(--n-amber);border-left:2px solid var(--n-amber);}
  .ha-ok{background:rgba(34,255,136,.06);color:var(--n-green);border-left:2px solid var(--n-green);}
  .hst-hero{display:flex;gap:8px;justify-content:center;padding:3px 4px;font:500 7px var(--mono);color:var(--n-td);border-top:1px solid rgba(0,255,204,.1);background:var(--n-s0);flex-wrap:wrap;}
  .mw-hero{height:380px;}
  .map-overlay{position:absolute;top:32px;right:6px;z-index:1000;pointer-events:none;}
  .map-ol-section{background:rgba(6,10,16,.88);border:1px solid rgba(0,255,204,.15);border-radius:3px;padding:3px 5px;backdrop-filter:blur(4px);}
  .map-ol-title{font:700 6px var(--mono);color:var(--n-teal);letter-spacing:.08em;padding-bottom:2px;border-bottom:1px solid var(--n-b);}
  .map-ol-row{display:flex;justify-content:space-between;gap:8px;padding:1px 0;}
  .map-ol-label{font:500 6px var(--mono);color:var(--n-td);}
  .map-ol-val{font:600 7px var(--mono);color:var(--n-ts);}
  .map-drl .map-ol-label{color:var(--n-purple);}
  .map-drl .map-ol-val{color:var(--n-purple);}
  .nmea-hero{font:400 7px var(--mono);color:var(--n-td);padding:2px 6px;background:var(--n-s0);border-top:1px solid rgba(0,255,204,.1);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .nmea-label{font-weight:700;color:var(--n-ts);}
  .nmea-sep{color:var(--n-b);margin:0 2px;}

  /* LSTM/TWIN ENGINE/EDGE */
  .lstm-strip{display:grid;grid-template-columns:1fr 1fr 1fr;gap:3px;}
  .lstm-mse{font:700 16px var(--mono);line-height:1;}
  .lstm-thr{font:500 7px var(--mono);color:var(--n-td);}
  .lstm-pred{font:600 8px var(--mono);}
  .engine-dual{display:flex;gap:8px;justify-content:center;margin:4px 0;}
  .eng-box{display:flex;flex-direction:column;align-items:center;padding:3px 6px;border-radius:3px;border:1px solid var(--n-b);background:var(--n-s2);min-width:70px;}
  .eng-label{font:600 6px var(--mono);color:var(--n-td);letter-spacing:.06em;}
  .eng-status{font:700 8px var(--mono);}
  .eng-healthy{color:var(--n-green);border-color:rgba(34,255,136,.2);}
  .eng-warning{color:var(--n-amber);border-color:rgba(255,170,51,.2);}
  .eng-fault{color:var(--n-red);border-color:rgba(255,51,68,.2);animation:critPulse 2s infinite;}
  .solas-toggle{display:flex;align-items:center;gap:6px;padding:3px 6px;background:var(--n-s2);border:1px solid rgba(255,51,68,.2);border-radius:3px;margin:2px 0;}
  .solas-label{font:700 7px var(--mono);color:var(--n-red);letter-spacing:.06em;}
  .solas-status{font:600 7px var(--mono);}
  .net-tiers{display:flex;gap:4px;margin:3px 0;}
  .net-tier{flex:1;padding:2px 4px;border-radius:2px;border:1px solid var(--n-b);text-align:center;}
  .net-tier.active{border-color:rgba(0,255,204,.3);background:rgba(0,255,204,.06);}
  .net-tier-label{font:600 6px var(--mono);color:var(--n-td);letter-spacing:.04em;display:block;}
  .net-tier-val{font:700 7px var(--mono);color:var(--n-teal);display:block;}

  /* CII */
  .cii-b{padding:3px;}
  .cii-rtg{display:flex;gap:8px;justify-content:center;margin-bottom:3px;}
  .cii-bx{display:flex;flex-direction:column;align-items:center;gap:0;}
  .cii-bl{font:600 6px var(--mono);color:var(--n-td);letter-spacing:.06em;}
  .cii-lt{font:800 20px var(--mono);line-height:1;}
  .cii-nm{font:600 8px var(--mono);color:var(--n-ts);}
  .cii-sp{width:1px;background:var(--n-b);}
  .cii-sc{margin:3px 0;}
  .cii-sb{display:flex;height:12px;border-radius:2px;overflow:hidden;}
  .cii-sg{flex:1;display:flex;align-items:center;justify-content:center;font:700 7px var(--mono);color:#fff;}
  .cii-ref{font:500 6px var(--mono);color:var(--n-td);margin-top:1px;}
  .cii-grid{display:grid;grid-template-columns:1fr 1fr;gap:0;}
  .cr{display:flex;justify-content:space-between;padding:1px 3px;border-bottom:1px solid rgba(22,32,48,.3);}
  .crl{font:500 7px var(--sans);color:var(--n-td);}.crv{font:600 7px var(--mono);color:var(--n-ts);}
  .tc{color:var(--n-teal);}.lc{color:var(--n-amber);}

  /* DRL */
  .drl-b{padding:3px;}
  .drl-sp{display:flex;align-items:center;gap:4px;justify-content:center;margin-bottom:3px;flex-wrap:wrap;}
  .drl-bx{display:flex;flex-direction:column;align-items:center;padding:2px 6px;background:var(--n-s2);border-radius:3px;border:1px solid var(--n-b);}
  .drl-rec{border-color:rgba(176,108,255,.3);}
  .drl-lb{font:600 5px var(--mono);color:var(--n-td);letter-spacing:.06em;}
  .drl-bg{font:700 14px var(--mono);color:var(--n-tp);line-height:1.1;}
  .drl-rec .drl-bg{color:var(--n-purple);}
  .drl-u{font:500 7px var(--mono);color:var(--n-td);}
  .drl-ar{font:700 12px var(--mono);color:var(--n-td);}
  .drl-dt{font:600 7px var(--mono);color:var(--n-ts);}

  .drl-trace{margin-top:3px;}.trace-l{font:600 6px var(--mono);color:var(--n-td);letter-spacing:.04em;}
  .trace-svg{width:100%;height:20px;}

  /* READOUTS */
  .rdts{padding:2px 4px;display:flex;flex-direction:column;gap:0;}
  .ro{display:flex;align-items:center;justify-content:space-between;padding:1px 0;border-bottom:1px solid rgba(22,32,48,.2);min-height:15px;flex-wrap:wrap;gap:2px;}
  .ro:last-child{border-bottom:none;}
  .ro-l{font:500 7px var(--sans);color:var(--n-td);}.ro-v{font:600 8px var(--mono);color:var(--n-ts);}
  .ro-v small{font-weight:400;color:var(--n-td);font-size:6px;}
  .ro-green{color:var(--n-green)!important;}.ro-amber{color:var(--n-amber)!important;}.ro-red{color:var(--n-red)!important;}.ro-purple{color:var(--n-purple)!important;}.ro-cyan{color:var(--n-cyan)!important;}.ro-teal{color:var(--n-teal)!important;}
  .ro-band{color:var(--n-green)!important;}
  .ro-bar{width:100%;height:2px;background:var(--n-s3);border-radius:1px;margin-top:0px;}
  .ro-bf{height:100%;border-radius:1px;transition:width .3s;}
  .ms{width:40px;height:10px;}

  /* CARDS */
  .cg{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:2px;}
  .cd h3{font:600 7px var(--mono);color:var(--n-ts);letter-spacing:.06em;margin:0;padding:3px 4px;background:var(--n-s0);border-bottom:1px solid var(--n-b);}
  .cd h3 small{font-weight:400;color:var(--n-td);}

  /* COMPASS */
  .compass-w{display:flex;align-items:center;gap:4px;padding:4px;}
  .compass-svg{width:120px;height:120px;flex-shrink:0;}
  .compass-data{flex:1;}

  /* RISK */
  .risk-b{padding:3px;}
  .risk-ov{display:flex;align-items:baseline;justify-content:center;gap:2px;margin-bottom:3px;}
  .risk-sc{font:700 22px var(--mono);line-height:1;}.risk-of{font:500 9px var(--mono);color:var(--n-td);}
  .rr{display:flex;align-items:center;gap:4px;padding:1px 0;}
  .rr-l{font:500 7px var(--sans);color:var(--n-td);min-width:50px;}
  .rr-b{flex:1;height:5px;background:var(--n-s3);border-radius:2px;overflow:hidden;}
  .rr-bf{height:100%;border-radius:2px;transition:width .5s;}
  .rr-v{font:600 7px var(--mono);color:var(--n-ts);min-width:16px;text-align:right;}

  /* STATUS */
  .sbar{display:flex;align-items:center;gap:8px;padding:2px 6px;background:var(--n-s0);border:1px solid var(--n-b);border-radius:3px;font:500 6px var(--mono);color:var(--n-td);overflow-x:auto;flex-wrap:nowrap;}
  .sb{white-space:nowrap;display:flex;align-items:center;gap:2px;}
  .sbd{width:4px;height:4px;border-radius:50%;background:var(--n-red);}
  .sb-on{background:var(--n-green);box-shadow:0 0 4px var(--n-green);}

  /* ALERTS COL */
  .ac{display:flex;flex-direction:column;gap:2px;padding:3px 3px 3px 0;max-height:calc(100vh - 56px);overflow-y:auto;}
  .ap{flex:1;display:flex;flex-direction:column;min-height:0;}
  .asum{display:flex;gap:3px;padding:2px 4px;border-bottom:1px solid var(--n-b);}
  .asb{font:700 7px var(--mono);padding:1px 3px;border-radius:2px;}
  .as-c{background:rgba(255,51,68,.12);color:var(--n-red);}.as-w{background:rgba(255,170,51,.12);color:var(--n-amber);}.as-a{background:rgba(176,108,255,.12);color:var(--n-purple);}.as-i{background:rgba(0,200,255,.12);color:var(--n-cyan);}
  .acnt{font:700 8px var(--mono);color:var(--n-td);margin-left:auto;background:var(--n-s3);padding:0 4px;border-radius:2px;}
  .alist{flex:1;overflow-y:auto;padding:2px;display:flex;flex-direction:column;gap:1px;}
  .ali{padding:2px 3px;border-radius:2px;border-left:2px solid transparent;}
  .ali-critical{border-left-color:var(--n-red);background:rgba(255,51,68,.04);}
  .ali-warning{border-left-color:var(--n-amber);background:rgba(255,170,51,.03);}
  .ali-advisory{border-left-color:var(--n-purple);background:rgba(176,108,255,.03);}
  .ali-info{border-left-color:var(--n-cyan);background:rgba(0,200,255,.02);}
  .ali-t{display:flex;align-items:center;gap:2px;}
  .ali-ic{font-size:6px;}.ali-sv{font:700 6px var(--mono);color:var(--n-td);}.ali-ct{font:700 6px var(--mono);color:var(--n-amber);}.ali-tm{font:400 6px var(--mono);color:var(--n-td);margin-left:auto;}
  .ali-msg{font:400 7px var(--sans);color:var(--n-ts);display:block;margin-top:0;line-height:1.2;}
  .ae{font:400 8px var(--sans);color:var(--n-td);padding:8px;text-align:center;}

  /* DIAGNOSTICS */
  .dp{max-height:180px;}

  /* LOADING */
  .ld{display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;gap:12px;background:var(--n-bg);}
  .ld-ring{width:28px;height:28px;position:relative;}
  .ld-ring div{position:absolute;width:28px;height:28px;border:2px solid transparent;border-top-color:var(--n-teal);border-radius:50%;animation:ldSpin 1.2s cubic-bezier(.5,0,.5,1) infinite;}
  .ld-ring div:nth-child(1){animation-delay:-.45s;}
  .ld-ring div:nth-child(2){animation-delay:-.3s;}
  .ld-ring div:nth-child(3){animation-delay:-.15s;}
  .ld-txt{font:500 10px var(--mono);color:var(--n-ts);}
  .ld-sub{font:400 8px var(--mono);color:var(--n-td);}

  :global(.wp-tt){background:var(--n-s2)!important;color:var(--n-ts)!important;border:1px solid var(--n-b)!important;font:500 7px var(--mono)!important;padding:1px 3px!important;border-radius:2px!important;box-shadow:none!important;}
  :global(.wp-tt::before){border-top-color:var(--n-b)!important;}

  /* WAYPOINT + RANGE LABELS */
  :global(.wp-label){background:none!important;border:none!important;box-shadow:none!important;}
  :global(.wp-label span){font:600 6px var(--mono);color:#00c8ff;opacity:.55;text-shadow:0 0 4px rgba(0,200,255,.3);letter-spacing:.06em;white-space:nowrap;pointer-events:none;}
  :global(.range-label){background:none!important;border:none!important;box-shadow:none!important;}
  :global(.range-label span){font:500 6px var(--mono);color:#00c8ff;opacity:.25;letter-spacing:.04em;white-space:nowrap;pointer-events:none;}

  /* ACCEPT GHOST ROUTE BUTTON */
  .ghost-accept-btn{padding:2px 6px;background:rgba(176,108,255,.15);border:1px solid rgba(176,108,255,.4);border-radius:3px;color:#b06cff;font:600 7px var(--mono);cursor:pointer;letter-spacing:.04em;transition:all .2s;}
  .ghost-accept-btn:hover{background:rgba(176,108,255,.3);border-color:rgba(176,108,255,.6);box-shadow:0 0 8px rgba(176,108,255,.2);}

  @keyframes ldSpin{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
  @keyframes ghostPulse{0%,100%{box-shadow:0 0 8px rgba(176,108,255,.1);}50%{box-shadow:0 0 16px rgba(176,108,255,.25);}}
  @keyframes critPulse{0%,100%{background:rgba(255,51,68,.06);}50%{background:rgba(255,51,68,.12);}}
  @keyframes bellPulse{0%,100%{box-shadow:0 0 4px rgba(255,51,68,.5);}50%{box-shadow:0 0 10px rgba(255,51,68,.9);}}

  /* ── Notification Bell ─────────────────────────────────────────── */
  .pt-bell{background:none;border:none;cursor:pointer;font-size:10px;position:relative;padding:2px 6px;color:var(--n-ts);}
  .pt-bell:hover{color:var(--n-tp);}
  .bell-dot{position:absolute;top:-2px;right:0;min-width:12px;height:12px;border-radius:6px;background:var(--n-red);color:#fff;font:700 6px var(--mono);
    display:inline-flex;align-items:center;justify-content:center;padding:0 2px;animation:bellPulse 2s infinite;}

  /* ── ICG Logo ────────────────────────────────────────────────── */
  .icg-logo{width:38px;height:auto;filter:drop-shadow(0 0 6px rgba(255,215,0,.35)) drop-shadow(0 0 12px rgba(0,255,204,.2));transition:filter .3s;}
  .nb:hover .icg-logo{filter:drop-shadow(0 0 10px rgba(255,215,0,.6)) drop-shadow(0 0 18px rgba(0,255,204,.4));}

  /* ── Live Telemetry Grid ───────────────────────────────────────── */
  .telem-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px;padding:4px 6px;}
  .telem-cell{background:var(--n-s1);border:1px solid var(--n-bdr);border-radius:3px;padding:5px 6px;display:flex;flex-direction:column;gap:1px;transition:border-color .3s,box-shadow .3s;}
  .telem-cell.telem-alert{border-color:var(--n-amber);box-shadow:inset 0 0 8px rgba(255,170,51,.15);}
  .telem-eng{font:600 6px var(--mono);color:var(--n-td);text-transform:uppercase;letter-spacing:.5px;}
  .telem-val{font:700 11px var(--mono);color:var(--n-tp);}
  .telem-tag{font:700 5.5px var(--mono);padding:1px 4px;border-radius:2px;width:fit-content;}
  .telem-ok{color:var(--n-green);background:rgba(34,255,136,.08);}
  .telem-warn{color:var(--n-amber);background:rgba(255,170,51,.12);animation:critPulse 2s infinite;}

  /* ── Propulsion Sync Hub ───────────────────────────────────────── */
  .prop-sync-hub{margin:0 0 4px 0;}
  .mcr-zone-w{display:flex;align-items:center;gap:8px;padding:4px 0 6px;}
  .mcr-lbl{font:600 7px var(--mono);color:var(--n-td);min-width:50px;}
  .mcr-bar{position:relative;flex:1;height:8px;background:var(--n-s1);border-radius:4px;border:1px solid var(--n-bdr);}
  .mcr-optimal{position:absolute;top:0;height:100%;background:rgba(34,255,136,.15);border-left:1px dashed var(--n-green);border-right:1px dashed var(--n-green);border-radius:0;}
  .mcr-ptr{position:absolute;top:-2px;width:3px;height:12px;background:var(--n-teal);border-radius:1px;transform:translateX(-50%);box-shadow:0 0 6px rgba(0,255,204,.5);}
  .mcr-val{font:700 9px var(--mono);min-width:40px;text-align:right;}

  /* ── DBSCAN KPIs ───────────────────────────────────────────────── */
  .dbscan-kpis{display:flex;gap:6px;margin:0 0 6px;flex-wrap:wrap;}
  .dbscan-kpi{flex:1;min-width:70px;background:var(--n-s1);border:1px solid var(--n-bdr);border-radius:3px;padding:4px 6px;}
  .dbscan-kl{font:500 6px var(--mono);color:var(--n-td);display:block;}
  .dbscan-kv{font:700 10px var(--mono);color:var(--n-tp);display:block;}
  .dbscan-kd{font:600 7px var(--mono);}

  /* ── Segment Classification Table ──────────────────────────────── */
  .seg-table-w{padding:0 6px 4px;overflow-x:auto;}
  .seg-table{width:100%;border-collapse:collapse;font:500 7px var(--mono);}
  .seg-table th{color:var(--n-td);text-align:left;padding:3px 6px;border-bottom:1px solid var(--n-bdr);font-size:6px;letter-spacing:.5px;}
  .seg-table td{padding:3px 6px;color:var(--n-ts);border-bottom:1px solid var(--n-s1);}
  .seg-mode{padding:1px 5px;border-radius:2px;font-weight:700;font-size:6.5px;}
  .seg-transit{color:var(--n-cyan);background:rgba(0,200,255,.1);}
  .seg-loiter{color:var(--n-amber);background:rgba(255,170,51,.1);}
  .seg-anchor{color:var(--n-td);background:var(--n-s1);}
  .seg-footer{padding:4px 0;text-align:right;font:500 6px var(--mono);}

  /* ── IMO DCS Report Button ─────────────────────────────────────── */
  .imo-btn{margin-left:auto;background:linear-gradient(135deg,var(--n-cyan),var(--n-teal));color:var(--n-bg);border:none;border-radius:3px;
    padding:2px 8px;font:700 6.5px var(--mono);cursor:pointer;letter-spacing:.3px;box-shadow:0 0 8px rgba(0,200,255,.25);transition:all .2s;}
  .imo-btn:hover{box-shadow:0 0 14px rgba(0,200,255,.5);transform:translateY(-1px);}

  /* ── Enhanced SOLAS Override ────────────────────────────────────── */
  .solas-toggle-enhanced{display:flex;align-items:center;justify-content:space-between;padding:4px 0;margin-bottom:4px;}
  .solas-toggle-enhanced.solas-active{background:rgba(255,51,68,.06);border-radius:3px;padding:4px 6px;box-shadow:0 0 12px rgba(255,51,68,.15);}
  .solas-btn{display:flex;align-items:center;gap:6px;background:none;border:1px solid var(--n-bdr);border-radius:3px;padding:2px 8px;cursor:pointer;transition:all .3s;}
  .solas-btn.solas-armed{border-color:var(--n-red);box-shadow:0 0 10px rgba(255,51,68,.3);}
  .solas-ind{font:700 7px var(--mono);color:var(--n-green);}
  .solas-armed .solas-ind{color:var(--n-red);animation:critPulse 2s infinite;}
  .solas-tk{width:24px;height:12px;background:var(--n-s2);border-radius:6px;position:relative;transition:background .3s;}
  .solas-th{width:10px;height:10px;border-radius:50%;background:var(--n-green);position:absolute;top:1px;left:1px;transition:all .3s;}
  .solas-th-on{left:13px;background:var(--n-red);box-shadow:0 0 6px rgba(255,51,68,.5);}

  /* ── Denoising Autoencoder Panel ───────────────────────────────── */
  .denoise-panel{padding:6px;margin-top:4px;border-top:1px solid var(--n-bdr);}
  .denoise-header{font:700 7px var(--mono);color:var(--n-teal);letter-spacing:.5px;margin-bottom:4px;}
  .denoise-mse{font:500 7px var(--mono);color:var(--n-ts);margin-bottom:6px;}
  .denoise-slider-w{margin-bottom:6px;}
  .denoise-lbl{display:flex;justify-content:space-between;font:500 6.5px var(--mono);color:var(--n-ts);margin-bottom:2px;}
  .denoise-pct{color:var(--n-teal);font-weight:700;}
  .denoise-range{width:100%;height:4px;-webkit-appearance:none;appearance:none;background:var(--n-s2);border-radius:2px;outline:none;cursor:pointer;}
  .denoise-range::-webkit-slider-thumb{-webkit-appearance:none;width:10px;height:10px;border-radius:50%;background:var(--n-teal);box-shadow:0 0 6px rgba(0,255,204,.4);cursor:pointer;}
  .denoise-range::-moz-range-thumb{width:10px;height:10px;border-radius:50%;background:var(--n-teal);box-shadow:0 0 6px rgba(0,255,204,.4);cursor:pointer;border:none;}
  .denoise-hint{font:400 5.5px var(--mono);color:var(--n-td);margin-top:1px;display:block;}

  /* ── EEXI Compliance Grid ──────────────────────────────────── */
  .eexi-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:3px;padding:4px 6px;}
  .eexi-card{display:flex;flex-direction:column;align-items:center;padding:4px 2px;background:var(--n-s2);border-radius:3px;border:1px solid var(--n-b);}
  .eexi-label{font:600 5.5px var(--mono);color:var(--n-td);letter-spacing:.06em;}
  .eexi-big{font:700 16px var(--mono);line-height:1.2;}
  .eexi-unit{font:500 6px var(--mono);color:var(--n-td);}

  /* ── EEXI Compliance Grid ──────────────────────────────────── */
  .eexi-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:3px;padding:4px 6px;}
  .eexi-card{display:flex;flex-direction:column;align-items:center;padding:4px 2px;background:var(--n-s2);border-radius:3px;border:1px solid var(--n-b);}
  .eexi-label{font:600 5.5px var(--mono);color:var(--n-td);letter-spacing:.06em;}
  .eexi-big{font:700 16px var(--mono);line-height:1.2;}
  .eexi-unit{font:500 6px var(--mono);color:var(--n-td);}
</style>
