import React, { useState, useEffect } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
    PieChart, Pie, Cell
} from 'recharts';
import {
    AlertTriangle, CheckCircle, RefreshCcw, Play, ShieldAlert,
    Activity, XCircle, Clock, Zap, FileText
} from 'lucide-react';
const API_BASE = import.meta.env.VITE_API_URL || 'https://recoverai-backend-h8rf.onrender.com';
const MOCK_LOW_RISK = { transaction_id: "demo_low", amount: 150.0, payment_method: "credit_card", customer_segment: "loyal", transaction_hour: 10, days_since_last_payment: 15, previous_failures: 0, retry_count: 0, checkout_duration: 30, device_type: "desktop", location_type: "domestic", payment_gateway: "razorpay", failure_reason: "None", subscription_status: "active", invoice_age_days: 0, amount_due: 150.0, payment_status: "failed" };
const MOCK_MED_RISK = {
    transaction_id: "demo_med",
    amount: 2000.0,
    payment_method: "upi",
    customer_segment: "returning",
    transaction_hour: 14,
    days_since_last_payment: 15,
    previous_failures: 0,
    retry_count: 1,
    checkout_duration: 30,
    device_type: "desktop",
    location_type: "domestic",
    payment_gateway: "razorpay",
    failure_reason: "network_error",
    subscription_status: "active",
    invoice_age_days: 0,
    amount_due: 2000.0,
    payment_status: "failed"
};
const MOCK_HIGH_RISK = { transaction_id: "demo_high", amount: 45000.0, payment_method: "net_banking", customer_segment: "new", transaction_hour: 3, days_since_last_payment: 90, previous_failures: 3, retry_count: 2, checkout_duration: 300, device_type: "mobile", location_type: "international", payment_gateway: "razorpay", failure_reason: "insufficient_funds", subscription_status: "none", invoice_age_days: 45, amount_due: 45000.0, payment_status: "failed" };

const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#6366f1'];

export default function Dashboard() {
    const [metrics, setMetrics] = useState(null);
    const [auditLog, setAuditLog] = useState([]);

    const [sandboxTxn, setSandboxTxn] = useState('demo_high');
    const [analysis, setAnalysis] = useState(null);
    const [isExecuting, setIsExecuting] = useState(false);
    const [executionResult, setExecutionResult] = useState(null);
    const [isBatchRunning, setIsBatchRunning] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const metricsRes = await fetch(`${API_BASE}/recovery/metrics`);
            const metricsData = await metricsRes.json();
            setMetrics(metricsData);

            const auditRes = await fetch(`${API_BASE}/recovery/audit`);
            const auditData = await auditRes.json();
            setAuditLog(auditData);
        } catch (e) {
            console.error("Failed to fetch data:", e);
        }
    };

    const handleAnalyze = async () => {
        try {
            setAnalysis(null);
            setExecutionResult(null);
            const payload = sandboxTxn === 'demo_low' ? MOCK_LOW_RISK : sandboxTxn === 'demo_med' ? MOCK_MED_RISK : MOCK_HIGH_RISK;

            // Phase 10 AI Agent structured endpoint
            const res = await fetch(`${API_BASE}/agent/decision`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            setAnalysis(data);
        } catch (e) {
            console.error("Analyze error:", e);
        }
    };

    const handleExecute = async () => {
        if (!analysis) return;
        setIsExecuting(true);
        try {
            const payload = sandboxTxn === 'demo_low' ? MOCK_LOW_RISK : sandboxTxn === 'demo_med' ? MOCK_MED_RISK : MOCK_HIGH_RISK;
            const res = await fetch(`${API_BASE}/recovery/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            setExecutionResult(data);
            fetchData(); // refresh metrics
        } catch (e) {
            console.error("Execute error:", e);
        }
        setIsExecuting(false);
    };

    const handleBatch = async () => {
        setIsBatchRunning(true);
        try {
            await fetch(`${API_BASE}/recovery/batch?limit=25`, { method: 'POST' });
            await fetchData();
        } catch (e) {
            console.error("Batch error:", e);
        }
        setIsBatchRunning(false);
    };

    const getRiskColor = (level) => {
        if (level === 'HIGH') return 'text-red-500 bg-red-500/10 border-red-500/20';
        if (level === 'MEDIUM') return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
        return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    };

    const statusColor = (status) => {
        if (status === 'SIMULATED_SUCCESS') return 'text-emerald-400';
        if (status === 'BLOCKED') return 'text-slate-400';
        if (status === 'FAILED' || status === 'FAILED_EXCEPTION') return 'text-red-400';
        if (status === 'ESCALATED') return 'text-amber-400';
        return 'text-slate-200';
    };

    const formatINR = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val || 0);

    const riskDist = auditLog.reduce((acc, curr) => {
        acc[curr.risk_level] = (acc[curr.risk_level] || 0) + 1;
        return acc;
    }, {});
    const pieData = Object.keys(riskDist).map(k => ({ name: k || 'UNKNOWN', value: riskDist[k] }));

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans p-6 overflow-x-hidden">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
                        <Activity className="text-emerald-500" /> RecoverAI Control Center
                    </h1>
                    <div className="mt-2 inline-flex items-center gap-2 px-3 py-1 rounded bg-slate-900 border border-slate-800 text-sm">
                        <ShieldAlert className="w-4 h-4 text-emerald-400" />
                        <span className="text-slate-300 font-medium">Razorpay TEST MODE • No real money moved</span>
                    </div>
                </div>
                <div className="flex gap-4">
                    <button onClick={fetchData} className="px-4 py-2 flex items-center gap-2 bg-slate-800 hover:bg-slate-700 rounded text-sm transition-colors border border-slate-700">
                        <RefreshCcw className="w-4 h-4" /> Refresh
                    </button>
                    <button onClick={handleBatch} disabled={isBatchRunning} className="px-5 py-2 flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium rounded transition-colors shadow-lg shadow-indigo-900/20">
                        {isBatchRunning ? <Clock className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        Run Synthetic Batch (25)
                    </button>
                </div>
            </div>

            {/* Metrics Row */}
            {metrics && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-slate-900 p-5 rounded-lg border border-slate-800 shadow-sm">
                        <div className="text-slate-400 text-sm font-medium mb-1">Total Risk Analyzed</div>
                        <div className="text-2xl font-bold text-white">{formatINR(metrics.total_at_risk_amount)}</div>
                        <div className="text-xs text-slate-500 mt-2">{metrics.total_transactions_analyzed} Transactions</div>
                    </div>
                    <div className="bg-slate-900 focus-within:ring-1 p-5 rounded-lg border border-emerald-900/50 shadow-sm relative overflow-hidden">
                        <div className="absolute top-0 right-0 bg-emerald-500/20 text-emerald-400 text-[10px] uppercase font-bold px-2 py-1 rounded-bl">SIMULATED</div>
                        <div className="text-slate-400 text-sm font-medium mb-1">Estimated Recovered</div>
                        <div className="text-2xl font-bold text-emerald-400">{formatINR(metrics.estimated_revenue_recovered)}</div>
                        <div className="text-xs text-emerald-500/70 mt-2">{metrics.successful_recoveries} Successes</div>
                    </div>
                    <div className="bg-slate-900 p-5 rounded-lg border border-slate-800 shadow-sm">
                        <div className="text-slate-400 text-sm font-medium mb-1">Recovery Rate</div>
                        <div className="text-2xl font-bold text-white">{metrics.recovery_rate}</div>
                        <div className="text-xs text-slate-500 mt-2">{metrics.stopped_actions} Action(s) Skipped/Blocked</div>
                    </div>
                    <div className="bg-slate-900 p-5 rounded-lg border border-slate-800 shadow-sm">
                        <div className="text-slate-400 text-sm font-medium mb-1">Escalated / Failed</div>
                        <div className="text-2xl font-bold text-amber-500">{metrics.escalated_cases} / {metrics.failed_actions}</div>
                        <div className="text-xs text-slate-500 mt-2">Required Human Intervention</div>
                    </div>
                </div>
            )}

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">

                {/* Left Col: Sandbox & Charts */}
                <div className="lg:col-span-1 flex flex-col gap-6">
                    {/* Action Sandbox */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 shadow-sm flex flex-col">
                        <div className="p-4 border-b border-slate-800 flex items-center gap-2">
                            <Zap className="w-5 h-5 text-indigo-400" />
                            <h2 className="font-semibold text-white">Recovery Sandbox</h2>
                        </div>
                        <div className="p-4 flex-1">
                            <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase">Select Mock Transaction</label>
                            <select
                                className="w-full bg-slate-950 border border-slate-800 text-sm p-2 rounded outline-none focus:border-indigo-500 mb-4"
                                value={sandboxTxn}
                                onChange={(e) => { setSandboxTxn(e.target.value); setAnalysis(null); setExecutionResult(null); }}
                            >
                                <option value="demo_low">demo_low (Low Risk, Success)</option>
                                <option value="demo_med">demo_med (Med Risk, Failed)</option>
                                <option value="demo_high">demo_high (High Risk, Failed)</option>
                            </select>

                            <button
                                onClick={handleAnalyze}
                                className="w-full bg-slate-800 hover:bg-slate-700 py-2 border border-slate-700 rounded text-sm mb-4 transition-colors">
                                Analyze w/ AI Engine
                            </button>

                            {analysis && (
                                <div className="bg-slate-950 p-4 rounded border border-slate-800 mb-4 text-sm shadow-inner">
                                    <div className="flex justify-between items-center mb-4">
                                        <span className="text-slate-400 font-medium">Predicted Risk Level:</span>
                                        <span className={`px-2 py-1 rounded border text-xs font-bold ${getRiskColor(analysis.risk_level)}`}>
                                            {analysis.risk_level} ({(analysis.risk_probability * 100).toFixed(1)}%)
                                        </span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4 mb-4">
                                        <div>
                                            <span className="block text-slate-400 text-xs mb-1">Recommended Action:</span>
                                            <span className="text-white font-mono bg-indigo-600/20 text-indigo-400 px-2 py-1 rounded-sm text-[11px] font-bold tracking-wider">{analysis.recommended_action}</span>
                                        </div>
                                        <div>
                                            <span className="block text-slate-400 text-xs mb-1">Human Review Req:</span>
                                            <span className={`font-mono px-2 py-1 rounded-sm text-[11px] font-bold tracking-wider ${analysis.requires_human_review ? 'bg-amber-500/20 text-amber-500' : 'bg-slate-800 text-slate-300'}`}>
                                                {analysis.requires_human_review ? "YES" : "NO"}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Expandable Why This Decision? */}
                                    <details className="mt-3 group border border-slate-800 rounded bg-slate-900/50">
                                        <summary className="text-xs text-slate-300 font-semibold p-2 cursor-pointer hover:bg-slate-800/50 outline-none flex items-center justify-between">
                                            <span>💡 Why this decision?</span>
                                            <span className="text-slate-500 transition group-open:rotate-180">▼</span>
                                        </summary>
                                        <div className="p-3 border-t border-slate-800 text-slate-400 text-xs flex flex-col gap-3 leading-relaxed">
                                            <p className="text-slate-300">{analysis.reasoning}</p>

                                            <div>
                                                <strong className="block text-white mb-1">Top Driving Factors:</strong>
                                                <ul className="list-disc pl-4 space-y-1">
                                                    {analysis.top_factors?.map((f, i) => (
                                                        <li key={i}>
                                                            <span className="text-indigo-300">{f.feature}</span>
                                                            <span className="text-slate-500 mx-1">({f.direction})</span>
                                                            <span className="opacity-50">— weight: {f.importance}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>

                                            <div>
                                                <strong className="block text-white mb-1">Deterministic Safety Checks:</strong>
                                                <div className="grid grid-cols-1 gap-1 font-mono text-[10px]">
                                                    <div className="flex justify-between"><span>Testing Safe Mode:</span> <span className={analysis.safety_checks.test_mode_only ? 'text-emerald-400' : 'text-red-400'}>{analysis.safety_checks.test_mode_only ? 'PASS' : 'FAIL'}</span></div>
                                                    <div className="flex justify-between"><span>Max Attempts OK:</span> <span className={analysis.safety_checks.maximum_attempts_ok ? 'text-emerald-400' : 'text-red-400'}>{analysis.safety_checks.maximum_attempts_ok ? 'PASS' : 'FAIL'}</span></div>
                                                    <div className="flex justify-between"><span>Not Previously Recovered:</span> <span className={analysis.safety_checks.payment_not_already_recovered ? 'text-emerald-400' : 'text-red-400'}>{analysis.safety_checks.payment_not_already_recovered ? 'PASS' : 'FAIL'}</span></div>
                                                </div>
                                            </div>
                                        </div>
                                    </details>
                                </div>
                            )}

                            {analysis && analysis.recommended_action !== 'NONE' && analysis.recommended_action !== 'BLOCKED' && analysis.recommended_action !== 'ESCALATE' && !executionResult && (
                                <button
                                    onClick={handleExecute} disabled={isExecuting}
                                    className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2 rounded text-sm transition-colors flex items-center justify-center gap-2">
                                    <CheckCircle className="w-4 h-4" /> Confirm & Execute Recovery
                                </button>
                            )}

                            {executionResult && (
                                <div className={`p-3 rounded text-sm border mt-4 ${executionResult.action_status === 'SIMULATED_SUCCESS' ? 'bg-emerald-900/20 border-emerald-500/20 text-emerald-400' : 'bg-amber-900/20 border-amber-500/20 text-amber-400'}`}>
                                    Result: <strong>{executionResult.action_status}</strong><br />
                                    <span className="text-xs opacity-75">{executionResult.stopping_rule_result}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="bg-slate-900 rounded-lg border border-slate-800 shadow-sm p-4 hidden md:block">
                        <h3 className="font-semibold text-white mb-4 text-sm uppercase tracking-wide text-slate-400">Decision Disribution</h3>
                        <div className="h-48">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60} fill="#8884d8">
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* Right Col: Audit Table */}
                <div className="lg:col-span-2 bg-slate-900 rounded-lg border border-slate-800 shadow-sm flex flex-col max-h-[700px]">
                    <div className="p-4 border-b border-slate-800 flex justify-between items-center">
                        <h2 className="font-semibold text-white flex items-center gap-2">
                            <FileText className="w-5 h-5 text-indigo-400" /> Live Audit Trail
                        </h2>
                        <span className="text-xs text-slate-400">{auditLog.length} Engine Events</span>
                    </div>
                    <div className="flex-1 overflow-auto p-4 custom-scrollbar">
                        {auditLog.length === 0 ? (
                            <div className="text-center text-slate-500 py-10 text-sm">No actions recorded yet. Run a batch simulation or use the sandbox.</div>
                        ) : (
                            <table className="w-full text-left text-sm">
                                <thead className="text-xs text-slate-400 uppercase bg-slate-950 sticky top-0 z-10">
                                    <tr>
                                        <th className="p-3 rounded-tl-lg font-semibold">Time</th>
                                        <th className="p-3 font-semibold">Txn ID</th>
                                        <th className="p-3 font-semibold">AI Risk</th>
                                        <th className="p-3 font-semibold">Action</th>
                                        <th className="p-3 rounded-tr-lg font-semibold">Status / Rule</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/50">
                                    {auditLog.map((log) => (
                                        <tr key={log.id} className="hover:bg-slate-800/50 transition-colors">
                                            <td className="p-3 text-slate-400 whitespace-nowrap">{new Date(log.created_at).toLocaleTimeString()}</td>
                                            <td className="p-3 font-mono text-xs text-slate-300">{log.transaction_id.slice(0, 10)}...</td>
                                            <td className="p-3">
                                                <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getRiskColor(log.risk_level)}`}>
                                                    {log.risk_level} ({(log.risk_probability * 100).toFixed(0)}%)
                                                </span>
                                            </td>
                                            <td className="p-3">
                                                <span className="font-mono text-xs text-indigo-300 bg-indigo-500/10 px-2 py-1 rounded">{log.selected_action}</span>
                                            </td>
                                            <td className="p-3">
                                                <div className={`font-medium ${statusColor(log.action_status)}`}>
                                                    {log.action_status}
                                                </div>
                                                <div className="text-[10px] text-slate-500 truncate max-w-[150px]">
                                                    {log.stopping_rule_result}
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
