"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";

function normalizeTheme(raw: string | null): "dark" | "light" {
    if (raw === "light") return "light";
    return "dark";
}

export default function ThemeToggle() {
    const [theme, setTheme] = useState<"dark" | "light">("dark");
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        let saved = localStorage.getItem("theme");
        if (saved === "default") {
            localStorage.setItem("theme", "dark");
            saved = "dark";
        }
        const next = normalizeTheme(saved);
        setTheme(next);
        document.documentElement.setAttribute("data-theme", next);
        setMounted(true);
    }, []);

    useEffect(() => {
        if (mounted) {
            document.documentElement.setAttribute("data-theme", theme);
        }
    }, [theme, mounted]);

    const toggleTheme = () => {
        const newTheme = theme === "dark" ? "light" : "dark";
        setTheme(newTheme);
        localStorage.setItem("theme", newTheme);
    };

    return (
        <button
            onClick={toggleTheme}
            type="button"
            className="p-2 text-muted hover:text-foreground transition-colors rounded-full hover:bg-surface/30"
            aria-label="Toggle Theme"
            title={theme === "dark" ? "Bytt til lys modus" : "Bytt til mørk modus"}
        >
            {!mounted || theme === "dark" ? (
                <Sun size={20} />
            ) : (
                <Moon size={20} />
            )}
        </button>
    );
}
