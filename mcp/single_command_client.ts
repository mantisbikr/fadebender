import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  // get command from args
  const commandText = process.argv[2] || "set track 1 volume to -24";

  const transport = new StdioClientTransport({
    command: "npx",
    args: ["tsx", "mcp/chrome_mcp_server.ts"],
  });

  const client = new Client(
    {
      name: "single-command-client",
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

    // Wait a bit for React to hydrate
    await new Promise((resolve) => setTimeout(resolve, 2000));

    console.log(`Typing command: "${commandText}"...`);
    // Assuming the standard chat input selector
    const selector = "input[placeholder*='Ask questions']"; 
    
    try {
        await client.callTool({
        name: "type",
        arguments: { 
            selector: selector,
            text: commandText 
        },
        });
    } catch (e) {
        // Fallback for different UI variations if needed, or just report
        console.log("Could not find specific input, trying generic input...");
        await client.callTool({
            name: "type",
            arguments: { 
                selector: "input",
                text: commandText 
            },
        });
    }

    console.log("Clicking submit...");
    await client.callTool({
      name: "click",
      arguments: { selector: "button[type='submit']" },
    });
    
    console.log("Command sent. Keeping browser open for 5 seconds to observe...");
    await new Promise((resolve) => setTimeout(resolve, 5000));

  } catch (error) {
    console.error("Error executing command:", error);
  } finally {
    await client.close();
    process.exit(0);
  }
}

main();
