import { z } from "zod";
import { MCPTool } from "@aicu/mcp-framework";

const { httpGet, downloadCsvData, sleep } = require("../xhs-browser.js");

/**
 * Input interface for GetNoteCommentsTool
 */
interface GetNoteCommentsInput {
  note_id: string;
  xsec_token: string;
  count: number;
  download: boolean;
}

/**
 * Comment data structure from Xiaohongshu API response
 */
interface CommentData {
  id: string;
  targetComment?: { id: string };
  userInfo: {
    nickname: string;
    userId: string;
    xsecToken: string;
  };
  ipLocation: string;
  likeCount: number;
  createTime: number;
  content: string;
  subComments?: CommentData[];
}

/**
 * API response structure for comment page
 */
interface CommentPageResponse {
  comments: CommentData[];
  cursor: string;
  xsecToken?: string;
}

/**
 * Tool for retrieving comment data from Xiaohongshu notes
 * Supports pagination, data export, and CSV download functionality
 */
class GetNoteCommentsTool extends MCPTool<GetNoteCommentsInput> {
  name = "Get Note Comments List";
  description = "Get comment list data for a specified Xiaohongshu note. Users can specify the number to retrieve (use -1 to get all). Users can also specify whether to export and download the data. Note: All parameters must be filled in, otherwise data cannot be retrieved.";

  schema = {
    note_id: {
      type: z.string(),
      description: "Note ID from Xiaohongshu",
    },
    xsec_token: {
      type: z.string(),
      description: "Security token for the note",
    },
    count: {
      type: z.number().min(-1).max(1000),
      default: 10,
      description: "Number of comments to retrieve. Default is 10. Use -1 to get all comments.",
    },
    download: {
      type: z.boolean(),
      default: false,
      description: "Whether to download and export comment data as CSV",
    }
  };

  /**
   * Execute the tool to retrieve note comments
   * @param input - Input parameters for comment retrieval
   * @returns Promise<string> - CSV data or download confirmation message
   */
  async execute(input: GetNoteCommentsInput): Promise<string> {
    const { note_id, count, download } = input;
    let xsec_token = input.xsec_token;
    
    try {
      let cursor = '';
      let result_arr: CommentData[] = [];
      
      // Paginate through all comments until we have enough or reach the end
      while (true) {
        console.log('[start]', count, cursor, xsec_token);
        
        // Check if we have retrieved enough comments
        if ((count !== -1) && (result_arr.length >= count)) break;
        
        let res: CommentPageResponse | null = null;
        try {
          const response = await httpGet(`/api/sns/web/v2/comment/page?note_id=${note_id}&cursor=${cursor}&top_comment_id=&image_formats=jpg,webp,avif&xsec_token=${encodeURIComponent(xsec_token)}`);
          res = response as CommentPageResponse;
        } catch (error) {
          console.error('Failed to fetch comments:', error);
          break;
        }
        
        console.log('res=', res);
        
        // Break if no more comments are available
        if (!res || !res.comments || res.comments.length === 0) break;
        
        result_arr = result_arr.concat(res.comments);
        cursor = res.cursor;
        
        // Add delay to avoid rate limiting
        await sleep(2);
      }

      // Generate CSV data from comments
      const csvData = this.generateCsvData(result_arr, note_id, count);
      
      if (download) {
        const downloadResult = downloadCsvData(`comments_${note_id}_${count}`, csvData);
        return downloadResult?.error 
          ? `Failed to save data: ${downloadResult.error}` 
          : `Data saved successfully. Count: ${result_arr.length}. File: ${downloadResult.link}`;
      }
      
      return csvData;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return `Failed to retrieve data! ${errorMessage}`;
    }
  }

  /**
   * Generate CSV data from comment array
   * @param comments - Array of comment data
   * @param noteId - Note ID for filename
   * @param count - Number of comments requested
   * @returns CSV formatted string
   */
  private generateCsvData(comments: CommentData[], noteId: string, count: number): string {
    let result_csv = 'comment_id,reply_comment_id,user_name,user_id,user_xsec_token,ip_location,like_count,created,content\n';
    let csv_arr: string[] = [];
    
    comments.forEach(comment => {
      // Process main comment
      const topComment = [
        comment.id, 
        comment.targetComment?.id || '',
        comment.userInfo.nickname, 
        comment.userInfo.userId, 
        comment.userInfo.xsecToken,
        comment.ipLocation,
        comment.likeCount,
        new Date(comment.createTime).toLocaleString(),
        comment.content
      ].map(field => String(field).includes(',') ? `"${field}"` : field);
      
      csv_arr.push(topComment.join(','));
      
      // Process sub-comments if they exist
      if (comment.subComments && comment.subComments.length > 0) {
        comment.subComments.forEach(subComment => {
          const subCommentRow = [
            subComment.id, 
            subComment.targetComment?.id || '',
            subComment.userInfo.nickname, 
            subComment.userInfo.userId, 
            subComment.userInfo.xsecToken,
            subComment.ipLocation,
            subComment.likeCount,
            new Date(subComment.createTime).toLocaleString(),
            subComment.content
          ].map(field => String(field).includes(',') ? `"${field}"` : field);
          
          csv_arr.push(subCommentRow.join(','));
        });
      }
    });
    
    result_csv += csv_arr.join('\n');
    return result_csv;
  }
}

module.exports = GetNoteCommentsTool;