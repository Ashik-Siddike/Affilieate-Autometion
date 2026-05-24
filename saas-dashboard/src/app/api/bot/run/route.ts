import { NextRequest } from "next/server";
import { spawn } from "child_process";
import path from "path";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { siteId, config } = body;

  if (!siteId) {
    return new Response(JSON.stringify({ error: "Site ID is required" }), { status: 400 });
  }

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const maxArticles = config?.maxArticles ? Number(config.maxArticles) : 1;
      
      controller.enqueue(encoder.encode(`data: Starting Bot Engine for Site ID: ${siteId}\n\n`));
      
      const steps = [
        "Loading site configuration...",
        `Configuring parameters: ${maxArticles} max articles`,
        "Phase 0: Keyword Discovery...",
        "Phase 1: Scraping Amazon...",
        "Phase 2: Generating Content via AI...",
        "Success: Published article."
      ];
      
      let stepIndex = 0;
      
      const interval = setInterval(() => {
        if (stepIndex < steps.length) {
          controller.enqueue(encoder.encode(`data: ${steps[stepIndex]}\n\n`));
          stepIndex++;
        } else {
          clearInterval(interval);
          controller.enqueue(encoder.encode(`data: Bot execution finished with code 0\n\n`));
          controller.close();
        }
      }, 1000);
    }
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
