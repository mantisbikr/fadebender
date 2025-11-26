import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { z } from "zod";

async function main() {
  const transport = new StdioClientTransport({
    command: "tsx",
    args: ["chrome_mcp_server.ts"],
  });

  const client = new Client(
    {
      name: "test-client",
      version: "1.0.0",
    },
    {
      capabilities: {},
    }
  );

  try {
    await client.connect(transport);
    console.log("Connected to Chrome MCP Server");

    console.log("Navigating to localhost:3000...");
    await client.callTool({
      name: "navigate",
      arguments: { url: "http://localhost:3000" },
    });

    // Wait a bit for React to hydrate (simple delay for test)
    await new Promise((resolve) => setTimeout(resolve, 2000));

    console.log("Typing command...");
    // MUI input often has a specific placeholder
    const selector = "input[placeholder*='Ask questions']"; 
    await client.callTool({
      name: "type",
      arguments: { 
        selector: selector,
        text: "set track 1 volume to -6" 
      },
    });

    console.log("Clicking submit...");
    await client.callTool({
      name: "click",
      arguments: { selector: "button[type='submit']" },
    });
    
    // Wait for response processing
    await new Promise((resolve) => setTimeout(resolve, 2000));

    console.log("Reading content...");
    const result = await client.callTool({
      name: "get_content",
      arguments: { format: "text" },
    });

    // @ts-ignore
    const content = result.content[0].text;
    console.log("Page Content Snippet:", content.substring(0, 500));
    
    if (content.includes("set track 1 volume to -6")) {
        console.log("SUCCESS: Found the typed command in the chat history!");
    } else {
        console.log("WARNING: Did not find the command in text (might be rendering delay).");
    }

    console.log("Waiting 10 seconds for visual inspection...");
    await new Promise((resolve) => setTimeout(resolve, 10000));

  } catch (error) {
    console.error("Error:", error);
  } finally {
    await client.close();
  }
}

main();
