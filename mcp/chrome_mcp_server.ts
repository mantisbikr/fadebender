import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import puppeteer, { Browser, Page } from "puppeteer";
import { z } from "zod";

// Global state for the browser instance
let browser: Browser | null = null;
let page: Page | null = null;

const server = new Server(
  {
    name: "fadebender-chrome",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Helper to ensure browser is running
async function ensureBrowser() {
  if (!browser) {
    try {
      // Try to connect to an existing browser instance first
      browser = await puppeteer.connect({
        browserURL: "http://127.0.0.1:9222",
      });
      // console.error("Connected to existing browser.");
    } catch (err) {
      // console.error("Could not connect to existing browser, launching new one:", err);
      browser = await puppeteer.launch({
        headless: false, // Visible for debugging/demo
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
      });
    }
    const pages = await browser.pages();
    // Prefer the first page, or create a new one if none exist
    page = pages[0] || (await browser.newPage());
  }
  return { browser, page: page! };
}

// Define Tool Schemas
const NavigateSchema = z.object({
  url: z.string().url(),
});

const ClickSchema = z.object({
  selector: z.string(),
});

const TypeSchema = z.object({
  selector: z.string(),
  text: z.string(),
});

const ScreenshotSchema = z.object({
  path: z.string().optional(), // If not provided, returns base64
});

const EvaluateSchema = z.object({
  script: z.string(),
});

// List Tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "navigate",
        description: "Navigate the Chrome browser to a specific URL.",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string", description: "The URL to visit" },
          },
          required: ["url"],
        },
      },
      {
        name: "click",
        description: "Click an element on the page identified by a CSS selector.",
        inputSchema: {
          type: "object",
          properties: {
            selector: { type: "string", description: "CSS selector to click" },
          },
          required: ["selector"],
        },
      },
      {
        name: "type",
        description: "Type text into an input field identified by a CSS selector.",
        inputSchema: {
          type: "object",
          properties: {
            selector: { type: "string", description: "CSS selector of the input" },
            text: { type: "string", description: "Text to type" },
          },
          required: ["selector", "text"],
        },
      },
      {
        name: "screenshot",
        description: "Take a screenshot of the current page.",
        inputSchema: {
          type: "object",
          properties: {
            path: { type: "string", description: "Optional file path to save to" },
          },
        },
      },
      {
        name: "evaluate",
        description: "Execute JavaScript in the browser context.",
        inputSchema: {
          type: "object",
          properties: {
            script: { type: "string", description: "JavaScript code to run" },
          },
          required: ["script"],
        },
      },
      {
        name: "get_content",
        description: "Get the textual content or HTML of the current page.",
        inputSchema: {
          type: "object",
          properties: {
            format: {
              type: "string",
              enum: ["text", "html", "markdown"],
              description: "Format to return (default: text)",
            },
          },
        },
      },
      {
        name: "close",
        description: "Close the browser.",
        inputSchema: { type: "object", properties: {} },
      },
    ],
  };
});

// Handle Tool Calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;

    if (name === "navigate") {
      const { url } = NavigateSchema.parse(args);
      const { page } = await ensureBrowser();
      await page.goto(url, { waitUntil: "domcontentloaded" });
      return {
        content: [{ type: "text", text: `Navigated to ${url}` }],
      };
    }

    if (name === "click") {
      const { selector } = ClickSchema.parse(args);
      const { page } = await ensureBrowser();
      try {
        await page.waitForSelector(selector, { timeout: 5000 });
        await page.click(selector);
        return {
          content: [{ type: "text", text: `Clicked ${selector}` }],
        };
      } catch (err) {
        throw new Error(`Failed to click '${selector}': ${(err as Error).message}`);
      }
    }

    if (name === "type") {
      const { selector, text } = TypeSchema.parse(args);
      const { page } = await ensureBrowser();
      try {
        await page.waitForSelector(selector, { timeout: 5000 });
        await page.type(selector, text);
        return {
          content: [{ type: "text", text: `Typed into ${selector}` }],
        };
      } catch (err) {
        throw new Error(`Failed to type into '${selector}': ${(err as Error).message}`);
      }
    }

    if (name === "screenshot") {
      const { path } = ScreenshotSchema.parse(args || {});
      const { page } = await ensureBrowser();
      if (path) {
        await page.screenshot({ path });
        return {
          content: [{ type: "text", text: `Screenshot saved to ${path}` }],
        };
      } else {
        const buffer = await page.screenshot({ encoding: "base64" });
        return {
          content: [
            {
              type: "image",
              data: buffer,
              mimeType: "image/png",
            },
          ],
        };
      }
    }

    if (name === "evaluate") {
      const { script } = EvaluateSchema.parse(args);
      const { page } = await ensureBrowser();
      const result = await page.evaluate((code) => {
        // eslint-disable-next-line no-eval
        return eval(code);
      }, script);
      return {
        content: [{ type: "text", text: JSON.stringify(result) }],
      };
    }

    if (name === "get_content") {
      const { format } = (args as { format?: string }) || {};
      const { page } = await ensureBrowser();
      
      let content = "";
      if (format === "html") {
        content = await page.content();
      } else if (format === "markdown") {
        // Simple heuristic for markdown-ish content
        content = await page.evaluate(() => {
          const TurndownService = (window as any).TurndownService;
          if (TurndownService) {
             return new TurndownService().turndown(document.body);
          }
          // Fallback to simple text if no library (could inject one, but keeping it simple)
          return document.body.innerText;
        });
      } else {
        // Default to text
        content = await page.evaluate(() => document.body.innerText);
      }

      return {
        content: [{ type: "text", text: content }],
      };
    }

    if (name === "close") {
      if (browser) {
        await browser.close();
        browser = null;
        page = null;
      }
      return {
        content: [{ type: "text", text: "Browser closed" }],
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${(error as Error).message}` }],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  // console.error("Fadebender Chrome MCP Server running on stdio");
}

main().catch((err) => {
  console.error("Fatal error in main():", err);
  process.exit(1);
});
