import React, { useMemo } from 'react';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { BarChart3, PieChart as PieChartIcon } from 'lucide-react';
import { LiquidCard } from './liquid.jsx';

const COLORS = ['#c4db46', '#91ad2d', '#d7e878', '#6f861f', '#a9c75b', '#e4ed9b', '#587016', '#b4ca70'];

function toNumber(value) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value !== 'string' || !value.trim()) return null;
  const parsed = Number(value.replace(/,/g, ''));
  return Number.isFinite(parsed) ? parsed : null;
}

function chartData(result) {
  if (result.status !== 'ok' || !Array.isArray(result.columns) || result.columns.length !== 2 || !Array.isArray(result.rows)) return null;
  const [first, second] = result.columns;
  const firstValues = result.rows.map((row) => row?.[0]);
  const secondValues = result.rows.map((row) => row?.[1]);
  const firstNumbers = firstValues.map(toNumber);
  const secondNumbers = secondValues.map(toNumber);
  const numericIndex = firstNumbers.every((value) => value !== null) ? 0 : secondNumbers.every((value) => value !== null) ? 1 : -1;
  if (numericIndex === -1 || result.rows.length < 2 || result.rows.length > 12) return null;

  const labelIndex = numericIndex === 0 ? 1 : 0;
  const valueIndex = numericIndex;
  const data = result.rows
    .map((row) => ({ label: String(row?.[labelIndex] ?? 'Unknown'), value: toNumber(row?.[valueIndex]) }))
    .filter((entry) => entry.value !== null);
  if (data.length < 2 || new Set(data.map((entry) => entry.label)).size !== data.length) return null;
  return {
    data,
    labelColumn: result.columns[labelIndex],
    valueColumn: result.columns[valueIndex],
    pie: data.length <= 8 && data.every((entry) => entry.value >= 0) && data.some((entry) => entry.value > 0),
  };
}

function shorten(value) {
  return value.length > 18 ? `${value.slice(0, 16)}…` : value;
}

export default function QueryVisualization({ result }) {
  const chart = useMemo(() => chartData(result), [result]);
  if (!chart) return null;

  return <LiquidCard animated={false} className="query-visualization">
    <div className="visualization-heading">
      <div>
        <div className="card-eyebrow">{chart.pie ? <PieChartIcon size={13} /> : <BarChart3 size={13} />} VISUAL SUMMARY</div>
        <h3>{chart.valueColumn} by {chart.labelColumn}</h3>
      </div>
      <span>Based on returned rows</span>
    </div>
    <div className="visualization-chart" aria-label={`Chart of ${chart.valueColumn} by ${chart.labelColumn}`}>
      <ResponsiveContainer width="100%" height={220}>
        {chart.pie
          ? <PieChart>
            <Pie data={chart.data} dataKey="value" nameKey="label" cx="50%" cy="50%" innerRadius={52} outerRadius={82} paddingAngle={2}>
              {chart.data.map((entry, index) => <Cell key={entry.label} fill={COLORS[index % COLORS.length]} />)}
            </Pie>
            <Tooltip formatter={(value) => Number(value).toLocaleString()} />
          </PieChart>
          : <BarChart data={chart.data} margin={{ top: 8, right: 8, left: 4, bottom: 32 }}>
            <XAxis dataKey="label" tickFormatter={shorten} angle={-25} textAnchor="end" interval={0} />
            <YAxis tickFormatter={(value) => Number(value).toLocaleString()} width={58} />
            <Tooltip formatter={(value) => Number(value).toLocaleString()} labelFormatter={(label) => `${chart.labelColumn}: ${label}`} />
            <Bar dataKey="value" name={chart.valueColumn} fill="#b9d43f" radius={[4, 4, 0, 0]} />
          </BarChart>}
      </ResponsiveContainer>
    </div>
  </LiquidCard>;
}
