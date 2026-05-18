import { Bell, Globe, Shield, User } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'

const settingsSections = [
  {
    icon: User,
    title: 'Profile',
    description: 'Manage your account and display preferences.',
    fields: [
      { label: 'Display name', value: 'Admin', type: 'text' },
      { label: 'Email', value: 'admin@naarfind.cloud', type: 'email' },
    ],
  },
  {
    icon: Bell,
    title: 'Notifications',
    description: 'Configure alert channels for fire events.',
    fields: [
      { label: 'Email alerts', value: true, type: 'toggle' },
      { label: 'SMS alerts', value: false, type: 'toggle' },
    ],
  },
  {
    icon: Globe,
    title: 'API',
    description: 'Connection settings for NaarFind Cloud API.',
    fields: [
      {
        label: 'API Base URL',
        value: import.meta.env.VITE_API_URL || 'http://localhost:8000',
        type: 'text',
        readOnly: true,
      },
    ],
  },
  {
    icon: Shield,
    title: 'Security',
    description: 'Authentication and access controls.',
    fields: [
      { label: 'Two-factor auth', value: false, type: 'toggle' },
    ],
  },
]

export default function Settings() {
  return (
    <div>
      <PageHeader
        title="Settings"
        description="Configure your NaarFind Cloud platform preferences."
      />

      <div className="space-y-6">
        {settingsSections.map((section) => (
          <section
            key={section.title}
            className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 sm:p-6"
          >
            <div className="mb-5 flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-orange-500/15 text-orange-400">
                <section.icon size={20} />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">{section.title}</h2>
                <p className="text-sm text-slate-500">{section.description}</p>
              </div>
            </div>

            <div className="space-y-4">
              {section.fields.map((field) => (
                <div
                  key={field.label}
                  className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
                >
                  <label className="text-sm font-medium text-slate-300">
                    {field.label}
                  </label>
                  {field.type === 'toggle' ? (
                    <button
                      type="button"
                      role="switch"
                      aria-checked={field.value}
                      className={`relative h-6 w-11 rounded-full transition ${
                        field.value ? 'bg-orange-500' : 'bg-slate-700'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white transition ${
                          field.value ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  ) : (
                    <input
                      type={field.type}
                      defaultValue={field.value}
                      readOnly={field.readOnly}
                      className="w-full max-w-xs rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-200 read-only:cursor-not-allowed read-only:opacity-70 focus:border-orange-500/50 focus:outline-none focus:ring-1 focus:ring-orange-500/30"
                    />
                  )}
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
