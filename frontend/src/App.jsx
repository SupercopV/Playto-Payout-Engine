import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Wallet, 
  ArrowUpRight, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  AlertCircle,
  RefreshCw,
  Plus
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const API_BASE = 'http://127.0.0.1:8000/api/v1';
const MERCHANT_ID = 1; // Default for demo

export default function App() {
  const [balances, setBalances] = useState({ available_balance: 0, held_balance: 0 });
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [amount, setAmount] = useState('');
  const [error, setError] = useState('');

  const fetchBalances = async () => {
    try {
      const res = await axios.get(`${API_BASE}/merchant/${MERCHANT_ID}/balance/`);
      setBalances(res.data);
    } catch (err) {
      console.error("Failed to fetch balances", err);
    }
  };

  const fetchPayouts = async () => {
    try {
      const res = await axios.get(`${API_BASE}/merchant/${MERCHANT_ID}/payouts/`);
      setPayouts(res.data);
    } catch (err) {
      console.error("Failed to fetch payouts", err);
    }
  };

  const initFetch = async () => {
    setLoading(true);
    await Promise.all([fetchBalances(), fetchPayouts()]);
    setLoading(false);
  };

  useEffect(() => {
    initFetch();
    const interval = setInterval(() => {
      fetchBalances();
      fetchPayouts();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handlePayout = async (e) => {
    e.preventDefault();
    setRequesting(true);
    setError('');
    
    try {
      const idempotencyKey = crypto.randomUUID();
      await axios.post(`${API_BASE}/payouts/`, {
        merchant_id: MERCHANT_ID,
        amount_paise: parseInt(amount) * 100 // Convert to paise
      }, {
        headers: { 'Idempotency-Key': idempotencyKey }
      });
      
      setAmount('');
      await initFetch();
    } catch (err) {
      console.error("Payout error:", err.response?.data);
      setError(err.response?.data?.error || "Failed to request payout");
    } finally {
      setRequesting(false);
    }
  };

  const formatMoney = (paise) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(paise / 100);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Playto Payout Engine</h1>
            <p className="text-slate-400">Merchant Dashboard • Alpha Corp</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-lg flex gap-1">
            <button onClick={initFetch} className="p-2 hover:bg-slate-800 rounded text-slate-400 transition-colors">
              <RefreshCw className={cn("w-5 h-5", loading && "animate-spin")} />
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Available Balance */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-emerald-500/10 rounded-xl">
                <Wallet className="w-6 h-6 text-emerald-500" />
              </div>
              <span className="text-xs font-medium text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded-full">Available</span>
            </div>
            <h3 className="text-slate-400 text-sm font-medium mb-1">Available Balance</h3>
            <p className="text-3xl font-bold text-white">{formatMoney(balances.available_balance)}</p>
          </div>

          {/* Held Balance */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 bg-amber-500/10 rounded-xl">
                <Clock className="w-6 h-6 text-amber-500" />
              </div>
              <span className="text-xs font-medium text-amber-500 bg-amber-500/10 px-2 py-1 rounded-full">Held</span>
            </div>
            <h3 className="text-slate-400 text-sm font-medium mb-1">Held Balance</h3>
            <p className="text-3xl font-bold text-white">{formatMoney(balances.held_balance)}</p>
          </div>

          {/* Request Payout Form */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
            <h3 className="text-white font-semibold mb-4">New Payout</h3>
            <form onSubmit={handlePayout} className="space-y-4">
              <div>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">₹</span>
                  <input 
                    type="number" 
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="Enter amount"
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pl-8 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-primary-500 transition-all"
                    required
                  />
                </div>
              </div>
              {error && (
                <div className="flex items-center gap-2 text-xs text-rose-500 bg-rose-500/10 p-2 rounded">
                  <AlertCircle className="w-3 h-3" />
                  {error}
                </div>
              )}
              <button 
                disabled={requesting || !amount}
                className="w-full bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg shadow-primary-600/20"
              >
                {requesting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                Request Payout
              </button>
            </form>
          </div>
        </div>

        {/* Payout History */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
          <div className="p-6 border-b border-slate-800 flex justify-between items-center">
            <h3 className="text-white font-semibold">Payout History</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-slate-500 text-sm border-b border-slate-800">
                  <th className="px-6 py-4 font-medium">Reference ID</th>
                  <th className="px-6 py-4 font-medium">Amount</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium">Requested At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {payouts.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">PAY-{p.id.toString().padStart(6, '0')}</td>
                    <td className="px-6 py-4 font-semibold text-slate-200">{formatMoney(p.amount_paise)}</td>
                    <td className="px-6 py-4">
                      <div className={cn(
                        "flex items-center gap-1.5 w-fit px-2.5 py-1 rounded-full text-xs font-medium",
                        p.status === 'completed' && "bg-emerald-500/10 text-emerald-500",
                        p.status === 'processing' && "bg-blue-500/10 text-blue-500",
                        p.status === 'pending' && "bg-slate-500/10 text-slate-400",
                        p.status === 'failed' && "bg-rose-500/10 text-rose-500",
                      )}>
                        {p.status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                        {p.status === 'processing' && <RefreshCw className="w-3 h-3 animate-spin" />}
                        {p.status === 'pending' && <Clock className="w-3 h-3" />}
                        {p.status === 'failed' && <XCircle className="w-3 h-3" />}
                        {p.status.charAt(0).toUpperCase() + p.status.slice(1)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      {new Date(p.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
                {payouts.length === 0 && !loading && (
                  <tr>
                    <td colSpan="4" className="px-6 py-12 text-center text-slate-500">
                      No payouts found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
