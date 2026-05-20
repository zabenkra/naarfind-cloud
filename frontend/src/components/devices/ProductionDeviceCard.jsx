import {
  Camera,
  Cpu,
  HardDrive,
  MemoryStick,
  Radio,
  Server,
  Thermometer,
} from 'lucide-react'
import StatusBadge from '../ui/StatusBadge'
import { formatDate, formatPercent } from '../../utils/format'

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="rounded-lg border border-slate-700/60 bg-slate-800/40 p-4">
      <div className="mb-2 flex items-center gap-2 text-slate-400">
        <Icon size={16} />
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-lg font-semibold text-slate-100">{value}</p>
    </div>
  )
}

export default function ProductionDeviceCard({ device }) {
  const temp =
    device.cpu_temp != null ? `${Number(device.cpu_temp).toFixed(1)}°C` : '—'

  return (
    <div className="overflow-hidden rounded-xl border border-amber-500/25 bg-gradient-to-br from-slate-900 via-slate-900 to-amber-950/20 shadow-lg">
      <div className="border-b border-amber-500/20 bg-amber-500/10 px-6 py-3">
        <p className="text-xs font-semibold uppercase tracking-widest text-amber-400">
          Production Device
        </p>
      </div>

      <div className="p-6">
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white">{device.name}</h2>
            <p className="mt-1 font-mono text-sm text-slate-400">{device.device_uid}</p>
            <p className="mt-2 text-sm text-slate-300">
              Site: <span className="text-slate-100">{device.site_name || '—'}</span>
            </p>
          </div>
          <div className="text-right">
            <StatusBadge status={device.status || 'offline'} />
            <p className="mt-2 text-xs text-slate-500">Last seen</p>
            <p className="text-sm text-slate-300">{formatDate(device.last_seen)}</p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Metric icon={Thermometer} label="CPU temp" value={temp} />
          <Metric icon={MemoryStick} label="RAM usage" value={formatPercent(device.ram_usage)} />
          <Metric icon={HardDrive} label="Disk usage" value={formatPercent(device.disk_usage)} />
          <Metric icon={Camera} label="Camera" value={device.camera_status || '—'} />
          <Metric icon={Server} label="Agent version" value={device.agent_version || '—'} />
          <Metric icon={Radio} label="Device ID" value={`#${device.id}`} />
        </div>

        <p className="mt-6 flex items-center gap-2 text-xs text-slate-500">
          <Cpu size={14} />
          Single Pi deployment — heartbeat every 30s from edge agent
        </p>
      </div>
    </div>
  )
}
