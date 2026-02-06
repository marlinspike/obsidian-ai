import { Sun, Moon, Monitor } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  const options = [
    { value: "light" as const, icon: Sun, label: "Light" },
    { value: "dark" as const, icon: Moon, label: "Dark" },
    { value: "system" as const, icon: Monitor, label: "System" },
  ];

  return (
    <div className="flex items-center gap-1 p-1 rounded-xl bg-[rgb(var(--muted))] border border-[rgb(var(--border))]">
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={`p-2 rounded-lg transition-all duration-200 ${
            theme === value
              ? "bg-[rgb(var(--card))] text-obsidian-600 dark:text-obsidian-400 shadow-sm"
              : "text-[rgb(var(--muted-foreground))] hover:text-[rgb(var(--foreground))]"
          }`}
          title={label}
        >
          <Icon className="h-4 w-4" />
        </button>
      ))}
    </div>
  );
}
