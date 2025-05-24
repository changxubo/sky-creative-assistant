import { MCPTool } from "@aicu/mcp-framework";
import { z } from "zod";

const {
  httpPost
} = require('../xhs-browser');

interface GetfeeddataInput {
  note_id: string;
  xsec_token: string;
}

class GetfeeddataTool extends MCPTool<GetfeeddataInput> {
  name = "get_note_details";
  description = "Get detailed data for a specific note, note_id and xsec_token are both required";

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

  async execute(input: GetfeeddataInput) {
    const { note_id, xsec_token } = input;
    try {
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
      // Format data
      const note = res['items'][0];
      const noteData = {
        note_id: note['id'],
        title: note['noteCard']['title'],
        desc: note['noteCard']['desc'],
        type: note['noteCard']['type'],
        user: note['noteCard']['user'],
        time: new Date(note['noteCard']['time']).toString(),
        counts: {
          collected: note['noteCard']['interactInfo']['collectedCount'],
          liked: note['noteCard']['interactInfo']['likedCount'],
          comment: note['noteCard']['interactInfo']['commentCount'],
          share: note['noteCard']['interactInfo']['shareCount']
        },
        images: [],
        video: {}
      }
      if (note['noteCard']['imageList']) {
        // @ts-ignore
        noteData['images'] = note['noteCard']['imageList'].map(i => i['urlDefault']);
      }
      if (note['noteCard']['video']) {
        let v = null;
        for (const key in note['noteCard']['video']['media']['stream']) {
          const vv = note['noteCard']['video']['media']['stream'][key];
          if (vv.length > 0) v = vv[0];
        };
        if (v) {
          noteData['video'] = {
            duration: note['noteCard']['video']['capa']['duration'],
            url: v['masterUrl']
          }
        }
      }
      // Convert to csv
      return JSON.stringify(noteData);
    } catch (e) {
      // @ts-ignore
      return 'Failed to get note data! ' + e.message;
    }
  }
}

module.exports = GetfeeddataTool;