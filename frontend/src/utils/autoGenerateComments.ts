import axios from 'axios';
import axiosInstance from '../api/axiosInstance';
import { fetchPlaceImage } from './fetchPlaceImage';

type AICommentResult = {
  mapbox_id: string;
  image_key_word?: string;
  comment?: string;
};

/**
 * Download an image URL as a File object so it can be uploaded via FormData.
 */
async function downloadImageAsFile(url: string): Promise<File | null> {
  try {
    const resp = await axios.get(url, { responseType: 'blob' });
    const blob = resp.data as Blob;
    const mimeType = blob.type || 'image/jpeg';
    const fileName = `ai-comment-img-${Date.now()}.jpg`;
    console.log('Downloaded image for AI comment:', fileName, mimeType);
    return new File([blob], fileName, { type: mimeType });
  } catch (err) {
    console.error('Failed to download image:', url, err);
    return null;
  }
}

/**
 * Fetch AI-generated comments for a given trip.
 * Then, for each comment:
 *   1) Get Unsplash images
 *   2) Download them as files
 *   3) Upload to /api/plans/comments/upload-images/
 *   4) Post comment to /api/plans/places/by-mapbox/${mapboxId}/comments/
 *
 * @param trip_id - The ID of the trip to generate comments for
 */
export async function autoGenerateComments(trip_id: number) {
  if (!trip_id) return;

  try {
    const res = await axiosInstance.get(
      `/api/plans/generate-ai-comments/${trip_id}/`
    );
    console.log('AI Comments generated:', res.data);
    const comment_results: AICommentResult[] = res.data;

    if (!comment_results || comment_results.length === 0) {
      console.warn('[autoGenerateComments] No AI comments returned.');
      return;
    }

    // Post each comment to backend
    for (const [idx, comment] of comment_results.entries()) {
      console.log(
        `[autoGenerateComments] Processing AI-comment ${idx + 1}/${comment_results.length}:`
      );

      const mapbox_id = comment.mapbox_id;
      const ai_comment = comment.comment;
      const image_key_word = comment.image_key_word;

      if (!mapbox_id) {
        console.warn(
          '[autoGenerateComments] Skipping invalid comment result:',
          comment
        );
        continue;
      }

      let finalImageUrls: string[] = [];
      if (image_key_word) {
        try {
          const unsplashImages = await fetchPlaceImage(image_key_word, 4);
          if (unsplashImages.length > 0) {
            // Download each image as File
            const files: File[] = [];
            for (let i = 0; i < unsplashImages.length; i++) {
              const file = await downloadImageAsFile(unsplashImages[i]);
              if (file) {
                files.push(file);
              }
            }

            const MAX_SIZE = 5 * 1024 * 1024; // 5MB
            const validFiles: File[] = [];

            for (const f of files) {
              if (!f.type.startsWith('image/')) {
                console.warn(
                  `[autoGenerateComments] Skipping non-image file: ${f.name}`
                );
                continue;
              }
              if (f.size > MAX_SIZE) {
                console.warn(
                  `[autoGenerateComments] Skipping file >5MB (${f.name}, size=${f.size})`
                );
                continue;
              }
              validFiles.push(f);
            }

            if (validFiles.length > 0) {
              // Upload images to backend
              const form = new FormData();
              validFiles.forEach((f) => form.append('images', f));
              form.append('mapbox_id', mapbox_id);

              try {
                const uploadResp = await axiosInstance.post(
                  '/api/plans/comments/upload-images/',
                  form,
                  {
                    headers: { 'Content-Type': 'multipart/form-data' },
                  }
                );

                const imgs = uploadResp.data?.images || [];
                const urls = imgs
                  .map((i: unknown) => {
                    if (typeof i === 'string') return i;
                    if (
                      i &&
                      typeof i === 'object' &&
                      'image_url' in (i as Record<string, unknown>)
                    ) {
                      const obj = i as Record<string, unknown>;
                      const v = obj['image_url'];
                      return typeof v === 'string' ? v : undefined;
                    }
                    return undefined;
                  })
                  .filter(Boolean) as string[];

                finalImageUrls = urls.slice(0, 4);
              } catch (err) {
                console.error(
                  `[autoGenerateComments] Failed to upload images for place ${idx + 1}/${comment_results.length}`,
                  err
                );
              }
            }
          } else {
            console.log(
              `[autoGenerateComments] No Unsplash images found for keyword "${image_key_word}"`
            );
          }
        } catch (err) {
          console.error(
            '[autoGenerateComments] Error fetching Unsplash images:',
            err
          );
        }
      }

      // Post comment + images to backend
      try {
        await axiosInstance.post(
          `/api/plans/places/by-mapbox/${encodeURIComponent(
            mapbox_id
          )}/comments/`,
          {
            text: ai_comment?.trim() || '',
            image_urls: finalImageUrls,
          }
        );
        console.log(
          `[autoGenerateComments] Posted comment for place ${idx + 1}/${comment_results.length}`
        );
      } catch (err) {
        console.error(
          `[autoGenerateComments] Failed to post comment for place ${idx + 1}/${comment_results.length}`,
          err
        );
      }
    }
  } catch (err) {
    console.error('autoGenerateComments: Failed overall', err);
  }
}
