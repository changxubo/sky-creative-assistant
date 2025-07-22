import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const { httpPost } = require('../xhs-browser');

/**
 * Input interface for retrieving note feed data
 */
interface GetFeedDataInput {
  note_id: string;
  xsec_token: string;
}

/**
 * Tool for retrieving detailed note data from XHS (Xiaohongshu) API
 * Handles fetching note metadata, user information, interaction counts, and media content
 */
class GetFeedDataTool extends MCPTool<GetFeedDataInput> {
  /**
   * Tool name displayed in the MCP framework
   */
  name = "get_note_details";
  
  /**
   * Tool description explaining its functionality and required parameters
   */
  description = "Get detailed data for a specific note, note_id and xsec_token are both required";

  /**
   * Schema definition for input validation
   */
  schema = {
    note_id: {
      type: z.string(),
      description: "The note_id of the note",
    },
    xsec_token: {
      type: z.string(),
      description: "The xsec_token corresponding to the note",
    },
  };

  /**
   * Execute the feed data retrieval operation
   * @param input - Contains note_id and xsec_token for API request
   * @returns Promise<string> - JSON stringified note data or error message
   */
  async execute(input: GetFeedDataInput) {
    const { note_id, xsec_token } = input;
    
    // Validate required parameters
    if (!note_id || !xsec_token) {
      return 'Failed to get note data! Missing required parameters: note_id or xsec_token';
    }
    
    try {
      // Make API request to XHS feed endpoint
      const res = await httpPost("/api/sns/web/v1/feed", {
        "source_note_id": note_id,
        "image_formats": [
          "jpg",
          "webp",
          "avif"
        ],
        "extra": {
          "need_body_topic": "1"
        },
        "xsec_source": "pc_feed",
        "xsec_token": xsec_token
      });
      
      // Validate API response structure
      if (!res || !res.items || res.items.length === 0) {
        return 'Failed to get note data! No items found in response';
      }
      
      // Extract note data from response
      const note = res.items[0];
      if (!note || !note.noteCard) {
        return 'Failed to get note data! Invalid note structure in response';
      }
      
      // Format structured note data
      const noteData = this.formatNoteData(note);
      
      // Return JSON stringified data
      return JSON.stringify(noteData);
    } catch (error) {
      // Enhanced error handling with type safety
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return `Failed to get note data! ${errorMessage}`;
    }
  }

  /**
   * Format raw note data into structured format
   * @param note - Raw note data from API response
   * @returns Formatted note data object
   */
  private formatNoteData(note: any) {
    const noteData = {
      note_id: note.id,
      title: note.noteCard?.title || '',
      desc: note.noteCard?.desc || '',
      type: note.noteCard?.type || '',
      user: note.noteCard?.user || {},
      time: note.noteCard?.time ? new Date(note.noteCard.time).toString() : '',
      counts: {
        collected: note.noteCard?.interactInfo?.collectedCount || 0,
        liked: note.noteCard?.interactInfo?.likedCount || 0,
        comment: note.noteCard?.interactInfo?.commentCount || 0,
        share: note.noteCard?.interactInfo?.shareCount || 0
      },
      images: [],
      video: {}
    };

    // Process image data if available
    if (note.noteCard?.imageList) {
      noteData.images = note.noteCard.imageList.map((image: any) => image.urlDefault || '');
    }

    // Process video data if available
    if (note.noteCard?.video) {
      const videoData = this.extractVideoData(note.noteCard.video);
      if (videoData) {
        noteData.video = videoData;
      }
    }

    return noteData;
  }

  /**
   * Extract video data from note card
   * @param video - Video data from note card
   * @returns Video data object or null
   */
  private extractVideoData(video: any) {
    if (!video.media?.stream) {
      return null;
    }

    // Find the first available video stream
    let videoStream = null;
    for (const key in video.media.stream) {
      const streamArray = video.media.stream[key];
      if (streamArray && streamArray.length > 0) {
        videoStream = streamArray[0];
        break;
      }
    }

    if (!videoStream) {
      return null;
    }

    return {
      duration: video.capa?.duration || 0,
      url: videoStream.masterUrl || ''
    };
  }
}

module.exports = GetFeedDataTool;