"use client";

import { useEffect, useState } from "react";
import { getConfig } from "@/lib/api";
import type { AppConfig } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Circle } from "lucide-react";

export function Header({ title }: { title: string }) {
  const [config, setConfig] = useState<AppConfig | null>(null);

  useEffect(() => {
    getConfig()
      .then((res) => setConfig(res.data))
      .catch(() => {});
  }, []);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-sm">
      <h1 className="text-xl font-semibold">{title}</h1>
      {config && (
        <div className="flex items-center gap-2">
          {Object.entries(config.services).map(([key, active]) => (
            <Badge
              key={key}
              variant={active ? "default" : "secondary"}
              className="gap-1 text-[10px]"
            >
              <Circle
                className={`h-1.5 w-1.5 fill-current ${active ? "text-green-400" : "text-muted-foreground"}`}
              />
              {key.replace(/_/g, " ")}
            </Badge>
          ))}
        </div>
      )}
    </header>
  );
}
