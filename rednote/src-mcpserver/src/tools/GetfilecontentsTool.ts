import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";
import fs from 'node:fs';

interface GetfilecontentsInput {
  filePath: string;
}

class GetfilecontentsTool extends MCPTool<GetfilecontentsInput> {
  name = "get_file_contents";
  description = "Get the contents of a local file at the specified path, returns the file's string data";

  schema = {
    filePath: {
      type: z.string(),
      required: true,
      description: "The local path of the file to read (absolute path)",
    },
  };

  async execute(input: GetfilecontentsInput) {
    const { filePath } = input;
    try {
      const data = fs.readFileSync(filePath).toString('utf-8');
      return data;
    } catch(e: any) {
      return 'Failed to read file: ' + e.message;
    }
  }
}

module.exports = GetfilecontentsTool;