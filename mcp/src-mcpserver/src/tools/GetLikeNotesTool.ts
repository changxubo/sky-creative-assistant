import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

// Local imports
const { httpGet, sleep, jsonToCsv, downloadCsvData } = require("../xhs-browser.js");

/**
 * Input interface for GetUserLikedNotesTool
 * @interface GetUserLikedNotesInput
 */
interface GetUserLikedNotesInput {
  /** User ID, must be exactly 24 characters in length */
  user_id: string;
  /** Number of notes to retrieve, default is 5. Set to -1 to get all notes */
  count: number;
  /** Security token for request parameter validation */
  xsec_token: string;
  /** Whether to export data as a downloadable CSV file */
  download: boolean;
}

/**
 * Structured note data returned from the API
 * @interface NoteData
 */
interface NoteData {
  note_id: string;
  title: string;
  type: string;
  user: {
    id: string;
    nick_name: string;
  };
  xsec_token: string;
  liked_count: number;
  cover: string;
}

/**
 * API response structure from the liked notes endpoint
 * @interface ApiResponse
 */
interface ApiResponse {
  notes: Array<{
    noteId: string;
    displayTitle: string;
    type: string;
    user: {
      userId: string;
      nickName: string;
    };
    xsecToken: string;
    interactInfo: {
      likedCount: number;
    };
    cover: {
      urlPre: string;
    };
  }>;
  hasMore: boolean;
  cursor: string;
}

/**
 * Tool for retrieving a user's liked notes from the platform
 * Implements proper error handling, input validation, and data sanitization
 * 
 * @class GetUserLikedNotesTool
 * @extends MCPTool<GetUserLikedNotesInput>
 */
class GetUserLikedNotesTool extends MCPTool<GetUserLikedNotesInput> {
  name = "Get User Liked Notes List";
  description = "Get a list of notes liked by the specified user. If the user needs to get their own account's list, please first get the current account's ID. If user ID is not specified, guide the user to provide an ID to continue. All parameters are required.";
  
  schema = {
    user_id: {
      type: z.string().length(24, "User ID must be exactly 24 characters"),
      description: "User ID, 24 characters in length"
    },
    count: {
      type: z.number().int().min(-1, "Count must be -1 or a positive integer"),
      default: 5,
      description: "Number of notes to retrieve, default is 5. To get all notes, set the value to -1"
    },
    xsec_token: {
      type: z.string().min(1, "xsec_token is required"),
      description: "xsec_token for request parameter validation, required for authentication"
    },
    download: {
      type: z.boolean(),
      description: 'Whether to export data as a file. If the user specifically requests a download, set to true, otherwise default is false',
      default: false
    }
  };

  /**
   * Executes the tool to retrieve user's liked notes
   * Implements proper error handling, input sanitization, and rate limiting
   * 
   * @param input - The input parameters for fetching liked notes
   * @returns Promise<string> - CSV data or download confirmation message
   * @throws Error when API calls fail or input validation fails
   */
  async execute(input: GetUserLikedNotesInput): Promise<string> {
    const { user_id, count, xsec_token, download } = input;
    
    // Input validation and sanitization
    if (!this.validateInputSecurity(user_id, xsec_token)) {
      return 'Error: Invalid or potentially malicious input detected';
    }
    
    const results: NoteData[] = [];
    let cursor = '';
    const maxRetries = 3;
    let retryCount = 0;

    try {
      while (true) {
        try {
          const apiResponse = await this.fetchLikedNotesPage(user_id, cursor, xsec_token);
          
          if (!apiResponse.notes || apiResponse.notes.length === 0) {
            break;
          }

          // Process and sanitize note data
          const processedNotes = this.processNoteData(apiResponse.notes, count, results.length);
          results.push(...processedNotes);

          // Check if we've reached the requested count
          if (count !== -1 && results.length >= count) {
            break;
          }

          // Check if there are more pages
          if (!apiResponse.hasMore) {
            break;
          }

          cursor = apiResponse.cursor;
          retryCount = 0; // Reset retry count on successful request
          
          // Rate limiting to prevent API abuse
          await sleep(2);

        } catch (error) {
          retryCount++;
          if (retryCount >= maxRetries) {
            throw new Error(`Failed to retrieve data after ${maxRetries} attempts: ${error instanceof Error ? error.message : 'Unknown error'}`);
          }
          
          // Exponential backoff for retries
          await sleep(Math.pow(2, retryCount) * 1000);
        }
      }

      return await this.formatAndReturnResults(results, user_id, count, download);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return `Failed to retrieve liked notes: ${errorMessage}`;
    }
  }

  /**
   * Validates input for security vulnerabilities
   * Checks for SQL injection, XSS, and other malicious patterns
   * 
   * @private
   * @param userId - User ID to validate
   * @param xsecToken - Security token to validate
   * @returns boolean - True if input is safe
   */
  private validateInputSecurity(userId: string, xsecToken: string): boolean {
    // Check for SQL injection patterns
    const sqlInjectionPattern = /('|\\')|(--|;)|(\s*(union|select|insert|update|delete|drop|create|alter|exec|execute)\s+)/i;
    
    // Check for XSS patterns
    const xssPattern = /<script|javascript:|on\w+\s*=/i;
    
    // Validate user ID format (should be alphanumeric)
    const userIdPattern = /^[a-zA-Z0-9]{24}$/;
    
    if (!userIdPattern.test(userId)) {
      return false;
    }
    
    if (sqlInjectionPattern.test(userId) || sqlInjectionPattern.test(xsecToken)) {
      return false;
    }
    
    if (xssPattern.test(userId) || xssPattern.test(xsecToken)) {
      return false;
    }
    
    return true;
  }

  /**
   * Fetches a single page of liked notes from the API
   * 
   * @private
   * @param userId - User ID to fetch notes for
   * @param cursor - Pagination cursor
   * @param xsecToken - Security token
   * @returns Promise<ApiResponse> - API response data
   */
  private async fetchLikedNotesPage(userId: string, cursor: string, xsecToken: string): Promise<ApiResponse> {
    const url = `/api/sns/web/v1/note/like/page?num=10&cursor=${cursor}&user_id=${userId}&image_formats=jpg,webp,avif&xsec_token=${encodeURIComponent(xsecToken)}&xsec_source=pc_feed`;
    
    const response = await httpGet(url);
    
    if (!response || typeof response !== 'object') {
      throw new Error('Invalid API response format');
    }
    
    return response as ApiResponse;
  }

  /**
   * Processes and sanitizes note data from API response
   * 
   * @private
   * @param notes - Raw note data from API
   * @param requestedCount - Number of notes requested
   * @param currentCount - Current number of processed notes
   * @returns NoteData[] - Processed and sanitized note data
   */
  private processNoteData(notes: ApiResponse['notes'], requestedCount: number, currentCount: number): NoteData[] {
    const processedNotes: NoteData[] = [];
    
    for (const note of notes) {
      // Stop if we've reached the requested count
      if (requestedCount > 0 && currentCount + processedNotes.length >= requestedCount) {
        break;
      }
      
      // Sanitize and validate note data
      const sanitizedNote: NoteData = {
        note_id: this.sanitizeString(note.noteId),
        title: this.sanitizeString(note.displayTitle),
        type: this.sanitizeString(note.type),
        user: {
          id: this.sanitizeString(note.user.userId),
          nick_name: this.sanitizeString(note.user.nickName)
        },
        xsec_token: this.sanitizeString(note.xsecToken),
        liked_count: Math.max(0, note.interactInfo?.likedCount || 0),
        cover: this.sanitizeUrl(note.cover?.urlPre)
      };
      
      processedNotes.push(sanitizedNote);
    }
    
    return processedNotes;
  }

  /**
   * Sanitizes string input to prevent XSS and other attacks
   * 
   * @private
   * @param input - String to sanitize
   * @returns string - Sanitized string
   */
  private sanitizeString(input: string): string {
    if (!input || typeof input !== 'string') {
      return '';
    }
    
    return input
      .replace(/[<>]/g, '') // Remove potential HTML tags
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .trim();
  }

  /**
   * Sanitizes URL input to ensure it's safe
   * 
   * @private
   * @param input - URL to sanitize
   * @returns string - Sanitized URL
   */
  private sanitizeUrl(input: string): string {
    if (!input || typeof input !== 'string') {
      return '';
    }
    
    try {
      // Validate URL format and protocol
      const url = new URL(input);
      if (!['http:', 'https:'].includes(url.protocol)) {
        return '';
      }
      return input;
    } catch {
      return '';
    }
  }

  /**
   * Formats results and returns them as CSV or download link
   * 
   * @private
   * @param results - Processed note data
   * @param userId - User ID for filename
   * @param count - Requested count for filename
   * @param download - Whether to download or return CSV
   * @returns Promise<string> - CSV data or download confirmation
   */
  private async formatAndReturnResults(results: NoteData[], userId: string, count: number, download: boolean): Promise<string> {
    const csvData = jsonToCsv(results, [
      'note_id', 'type', 'title', 'xsec_token', 'liked_count', 'cover', 
      'user_id@user.id', 'user_name@user.nick_name'
    ]);
    
    if (download) {
      const fileName = `user_likes_${userId}_${count}_${Date.now()}.csv`;
      const downloadResult = downloadCsvData(fileName, csvData);
      
      if (downloadResult.error) {
        throw new Error(`Failed to save data: ${downloadResult.error}`);
      }
      
      return `Data saved successfully. Count: ${results.length}. File: ${downloadResult.link}`;
    }
    
    return csvData;
  }
}

module.exports = GetUserLikedNotesTool;